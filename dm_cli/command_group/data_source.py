import json
from pathlib import Path

import emoji
import typer
from rich import print
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from typing_extensions import Annotated

from dm_cli.dmss import ApplicationException, dmss_api, dmss_exception_wrapper
from dm_cli.import_entity import import_folder_entity, remove_by_path_ignore_404
from dm_cli.utils.file_structure import get_app_dir_structure, get_json_files_in_dir
from dm_cli.utils.utils import (
    get_root_packages_in_data_sources,
    validate_entities_in_data_sources,
)

data_source_app = typer.Typer()


@data_source_app.command("import", help="Subcommand for working with data sources")
def import_data_source(
    path: Annotated[Path, typer.Argument(help="Path on local filesystem to a data source JSON file.")]
):
    """
    Import a single data source definition to DMSS.
    """

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
        retry=retry_if_not_exception_type(ApplicationException),
    )
    def retry_wrapper():
        data_source_path = Path(path)
        if not data_source_path.is_file():
            raise FileNotFoundError(f"The path '{path}' is not a file.")

        print(f"IMPORTING DATA SOURCE '{data_source_path.name}'")

        # Read the data source definition
        with open(data_source_path) as file:
            document = json.load(file)
            existing_data_sources = dmss_exception_wrapper(dmss_api.data_source_get_all)
            if any(existing_document["name"] == document["name"] for existing_document in existing_data_sources):
                print(f"WARNING: data source {document['name']} already exists. Updating existing data source.")

            dmss_exception_wrapper(dmss_api.data_source_save, document["name"], document)
            print(f"\tImported data source '{document['name']}' ✓")

    retry_wrapper()


@data_source_app.command("import-all", help="Import all datasources found in the directory given by 'path'")
def import_all_data_sources(
    path: Annotated[
        Path, typer.Argument(help="Path on local filesystem to the folder containing the data sources to import.")
    ]
):
    """
    Import all data source definitions to DMSS.
    """
    data_sources_dir = Path(path)
    if not data_sources_dir.is_dir():
        raise FileNotFoundError(f"The path '{path}' is not a directory.")

    print("IMPORTING DATA SOURCES")

    # List all data source definitions under <data_sources_dir>
    data_sources = get_json_files_in_dir(data_sources_dir)
    if not data_sources:
        print(emoji.emojize(f"\t:warning: No data source definitions were found in '{data_sources_dir}'"))

    for filename in data_sources:
        # Import the data source definition
        filepath = data_sources_dir.joinpath(filename)
        import_data_source(filepath)


@data_source_app.command("init")
def initialize_data_source(
    path: Annotated[Path, typer.Argument(help="Path on local filesystem to data source folder.")],
    validate_entities: Annotated[
        bool, typer.Option(help="If True, all entities uploaded to DMSS will be validated.")
    ] = True,
):
    """
    Initialize the data sources and import all packages.
    The packages in a data sources will be deleted before data sources are imported.
    """
    # Check for presence of expected directories, 'data_sources' and 'data'
    data_sources_dir, data_dir = get_app_dir_structure(Path(path))

    data_source_definitions = get_json_files_in_dir(data_sources_dir)
    if not data_source_definitions:
        print(emoji.emojize(f"\t:warning: No data source definitions were found in '{data_sources_dir}'."))
    for data_source_definition_filename in data_source_definitions:
        import_data_source_file(data_sources_dir, data_dir, data_source_definition_filename, False)
    data_source_contents = get_root_packages_in_data_sources(path)
    if validate_entities:
        dmss_exception_wrapper(validate_entities_in_data_sources, data_source_contents)


def import_data_source_file(
    data_sources_dir: str, data_dir: str, data_source_definition_filename: str, resolve_local_ids: bool
):
    data_source_definition_filepath = Path(data_sources_dir).joinpath(data_source_definition_filename)
    data_source_name = data_source_definition_filename.replace(".json", "")

    data_source_data_dir = data_dir / data_source_name
    if not data_source_data_dir.is_dir():
        print(
            emoji.emojize(
                f"\t:warning: No data source data directory was found by the name '{data_source_name}' in '{data_dir}'."
            )
        )
    else:
        import_data_source(data_source_definition_filepath)
        with open(data_source_definition_filepath) as file:
            data_source_document = json.load(file)
            global_folders = data_source_document.get("global_folders", [])
            root_packages = [f for f in data_source_data_dir.iterdir() if f.is_dir() and f.name not in global_folders]
            # Remove existing root packages from the data source.
            # This will also remove any files in the global folders that are references from files in the root packages.
            for root_package in root_packages:
                dmss_exception_wrapper(remove_by_path_ignore_404, f"/{data_source_name}/{root_package.name}")

            # Import all root packages
            for root_package in root_packages:
                print(f"Importing PACKAGE '{data_source_data_dir / root_package.name}' --> '{data_source_name}'")
                dmss_exception_wrapper(
                    import_folder_entity,
                    source_path=data_source_data_dir / root_package.name,
                    destination=data_source_name,
                    # Use the document raw endpoint,
                    # so that uploaded packages will not be resolved,
                    # this is to support uploading core blueprints.
                    raw_package_import=True,
                    resolve_local_ids=resolve_local_ids,
                )


@data_source_app.command("reset")
def reset_data_source(
    data_source: Annotated[str, typer.Argument(help="Name of data source to reset")],
    path: Annotated[Path, typer.Argument(help="Path on local filesystem to data source folder.")],
    resolve_local_ids: Annotated[bool, typer.Argument(help="Resolve local ids")] = False,
):
    """
    Reset a single data source (deletes and re-uploads root-packages)
    """
    app_dir = Path(path)
    if not app_dir.is_dir():
        raise FileNotFoundError(f"The path '{path}' is not a directory.")

    # Check for presence of expected directories, 'data_sources' and 'data'
    data_sources_dir, data_dir = get_app_dir_structure(app_dir)

    # Check for the data source definition file (json)
    data_source_path = data_sources_dir.joinpath(f"{data_source}.json")
    if not data_source_path.is_file():
        raise FileNotFoundError(f"There is no data source definition for '{data_source}' in '{data_sources_dir}'.")
    # Check for the data source data directory (contains packages)
    data_source_data_dir = data_dir.joinpath(data_source)
    if not data_source_data_dir.is_dir():
        raise FileNotFoundError(f"There is no data source directory for '{data_source}' in '{data_dir}'.")

    # Import all packages in the data source
    import_data_source_file(data_sources_dir, data_dir, f"{data_source}.json", resolve_local_ids)
