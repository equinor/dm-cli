import json
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from typing_extensions import Annotated

from dm_cli.dmss import ApplicationException, console, dmss_api, dmss_exception_wrapper
from dm_cli.dmss_api import ApiException
from dm_cli.import_entity import import_folder_entity, import_single_entity
from dm_cli.utils.utils import destination_is_root

entities_app = typer.Typer(help="Import, delete, or validate entities and/or blueprints")


@entities_app.command("import")
def import_entity(
    source: Annotated[
        str,
        typer.Argument(
            help="Path to file or folder on local filesystem to import. Trailing '/' will result in the content being imported instead of the folder itself."
        ),
    ],
    destination: Annotated[
        str,
        typer.Argument(
            help="Address for the folder or file. Should be on the format <DataSource>/<rootPackage>/<subPackage>/<entity>"
        ),
    ],
    validate: Annotated[bool, typer.Option(help="if True, all entities uploaded will be validated.")] = True,
) -> bool:
    """
    Import an entity (file or package) <source> to the given <destination>.
    """
    source_path = Path(source)
    destination = destination.rstrip("/\\")
    # Not replacing a package, but appending to. Can therefore not use "fast mode"
    fast = destination_is_root(Path(destination))

    def inner_import():
        if source_path.is_dir():
            # If source path ends with "/" or windows "\", import content instead of the package itself
            if source[-1] in ("/", "\\"):
                print(f"Importing all content from '{source}*' --> '{destination}'")
                for file in source_path.iterdir():
                    if file.is_file():
                        import_single_entity(file, destination, validate)
                        continue
                    import_folder_entity(file, destination, fast)
                    if validate:
                        print(f"Validating entities in: {destination}/{file.name}")
                        dmss_api.validate_existing_entity(f"{destination}/{file.name}")
                return True
            print(f"Importing PACKAGE '{source}' --> '{destination}'")
            import_folder_entity(source_path, destination, fast)
            if validate:
                print(f"Validating entities in: {destination}/{source_path.name}")
                dmss_api.validate_existing_entity(f"{destination}/{source_path.name}")
            return True
        else:
            import_single_entity(source_path, destination, validate)
            return True

    return dmss_exception_wrapper(inner_import)


@entities_app.command("import-batch")
def import_batch(
    data_directory: Annotated[
        Path,
        typer.Argument(
            help="Path to a directory laid out as <dataSource>/<rootPackage>. Every root package found is imported into the data source it is located under."
        ),
    ],
    exclude: Annotated[
        Optional[List[str]],
        typer.Option(help="Name of a data source to skip. Can be repeated."),
    ] = None,
    validate: Annotated[bool, typer.Option(help="if True, all entities uploaded will be validated.")] = True,
) -> bool:
    """
    Import every root package found under <data_directory> into its data source.

    This is equivalent to running 'entities import <data_directory>/<dataSource>/<rootPackage> <dataSource>'
    once per root package, but does so in a single process and over a single reused HTTP connection.
    """
    if not data_directory.is_dir():
        raise FileNotFoundError(f"The path '{data_directory}' is not a directory.")

    def visible_entries(directory: Path) -> list[Path]:
        # Hidden entries are skipped so that incidental files such as '.DS_Store'
        # are not mistaken for packages.
        return sorted(entry for entry in directory.iterdir() if not entry.name.startswith("."))

    excluded = set(exclude or [])
    for data_source_dir in visible_entries(data_directory):
        if not data_source_dir.is_dir():
            continue
        if data_source_dir.name in excluded:
            print(f"Skipping data source '{data_source_dir.name}'")
            continue
        for root_package in visible_entries(data_source_dir):
            import_entity(str(root_package), data_source_dir.name, validate)
    return True


@entities_app.command("validate")
def validate_entity(
    destinations: Annotated[
        List[str],
        typer.Argument(
            help="Addresses for the folders or files to validate. Should be on the format <DataSource>/<rootPackage>/<subPackage>/<entity>"
        ),
    ],
) -> bool:
    """Recursively validate one or more entities at remote targets"""

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_not_exception_type((ApplicationException, RuntimeError)),
    )
    def validation_error_wrapper(destination: str):
        try:
            dmss_api.validate_existing_entity(destination)
        except ApiException as e:
            exception_body = json.loads(e.body)
            if exception_body["type"] == "ValidationException":
                console.print(exception_body, style="red1")
                raise typer.Exit(code=1)
            raise e

    for destination in destinations:
        print(f"Validating entities recursively in: {destination}")
        # Validation is CPU bound on the DMSS side, so there is nothing to gain from validating targets
        # concurrently; doing so only makes the blueprint caches thrash.
        dmss_exception_wrapper(validation_error_wrapper, destination)


@entities_app.command("delete")
def delete_entity(
    target: Annotated[
        str,
        typer.Argument(
            help="Delete an entity from DMSS. Target should be an address on the format <DataSource>/<rootPackage>/<subPackage>/<entity>"
        ),
    ],
):
    """
    Delete an entity from DMSS.
    """

    dmss_exception_wrapper(dmss_api.document_remove, target)
