import json
from pathlib import Path

import emoji
import typer
from rich import print

from dm_cli.dmss import dmss_api, dmss_exception_wrapper
from dm_cli.dmss_api.exceptions import NotFoundException
from dm_cli.import_entity import import_folder_entity
from dm_cli.utils.file_structure import get_app_dir_structure, get_json_files_in_dir

data_source_app = typer.Typer()


@data_source_app.command("import", help="Subcommand for working with data sources")
def import_data_source(path: Path):
    """
    Import a single data source definition to DMSS.
    """
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


@data_source_app.command("import-all", help="Import all datasources found in the directory given by 'path'")
def import_all_data_sources(path: Path):
    """
    Import all data source definitions to DMSS
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


def remove_by_path_ignore_404(target: str):
    try:
        dmss_api.document_remove_by_path(target)
    except NotFoundException:
        pass


@data_source_app.command("init", help="Initialize the data sources and import all packages")
def initialize_data_source(path: Path):
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
        data_source_definition_filepath = Path(data_sources_dir).joinpath(data_source_definition_filename)
        data_source_name = data_source_definition_filename.replace(".json", "")

        data_source_data_dir = data_dir / data_source_name
        if not data_source_data_dir.is_dir():
            print(
                emoji.emojize(
                    f"\t:warning: No data source data directory was found by the name '{data_source_name}' in '{data_dir}'."
                )
            )
            continue

        import_data_source(data_source_definition_filepath)
        for root_package in [f for f in data_source_data_dir.iterdir() if f.is_dir()]:
            # Delete all packages in the data source
            dmss_exception_wrapper(remove_by_path_ignore_404, f"{data_source_name}/{root_package.name}")

            dmss_exception_wrapper(
                import_folder_entity,
                source_path=data_source_data_dir / root_package.name,
                destination=data_source_name,
            )


@data_source_app.command("reset")
def reset_data_source(data_source: str, path: Path):
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
    initialize_data_source(path)
