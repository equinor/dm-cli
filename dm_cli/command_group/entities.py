import json
from pathlib import Path

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
                        import_single_entity(file, destination)
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
            import_single_entity(source_path, destination)
            if validate:
                print(f"Validating entities in: {destination}/{source_path.name}")
                dmss_api.validate_existing_entity(f"{destination}/{source_path.name}")
            return True

    return dmss_exception_wrapper(inner_import)


@entities_app.command("validate")
def validate_entity(
    destination: Annotated[
        str,
        typer.Argument(
            help="Address for the folder or file. Should be on the format <DataSource>/<rootPackage>/<subPackage>/<entity>"
        ),
    ]
) -> bool:
    """Recursively validate entity at remote target"""
    print(f"Validating entities recursively in: {destination}")

    @retry(
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_not_exception_type((ApplicationException, RuntimeError)),
    )
    def validation_error_wrapper():
        try:
            dmss_api.validate_existing_entity(destination)
        except ApiException as e:
            exception_body = json.loads(e.body)
            if exception_body["type"] == "ValidationException":
                console.print(exception_body, style="red1")
                raise typer.Exit(code=1)
            raise e

    dmss_exception_wrapper(validation_error_wrapper)


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

    dmss_exception_wrapper(dmss_api.document_remove, target)
