from pathlib import Path

import typer
from rich import print
from typing_extensions import Annotated

from dm_cli.dmss import dmss_api, dmss_exception_wrapper
from dm_cli.import_entity import import_folder_entity, import_single_entity

entities_app = typer.Typer()


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
) -> bool:
    """
    Import an entity (file or package) <source> to the given <destination>.
    """
    source_path = Path(source)
    destination = destination.rstrip("/\\")
    if source_path.is_dir():
        # If source path ends with "/" or windows "\", import content instead of the package itself
        if source[-1] in ("/", "\\"):
            print(f"Importing all content from '{source}' --> '{destination}'")
            for file in source_path.iterdir():
                if file.is_file():
                    dmss_exception_wrapper(import_single_entity, file, destination)
                    continue
                dmss_exception_wrapper(import_folder_entity, file, destination, None)
            return True
        print(f"Importing PACKAGE '{source}' --> '{destination}'")
        dmss_exception_wrapper(import_folder_entity, source_path, destination, None)
        return True
    else:
        dmss_exception_wrapper(import_single_entity, source_path, destination)
        return True


@entities_app.command("delete")
def delete_entity(
    target: Annotated[
        str,
        typer.Argument(
            help="Delete an entity from DMSS. Target should be an address on the format <DataSource>/<rootPackage>/<subPackage>/<entity>"
        ),
    ]
):
    """
    Delete an entity from DMSS.
    """
    # TODO: Add exception handling
    dmss_api.document_remove(target)
