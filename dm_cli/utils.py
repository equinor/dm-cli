from dataclasses import dataclass
from os.path import normpath
from pathlib import Path
from typing import Dict, List, Literal, NewType
from zipfile import ZipFile

import click
import emoji


class ApplicationException(Exception):
    status: int = 500
    type: str = "ApplicationException"
    message: str = "The requested operation failed"
    debug: str = "An unknown and unhandled exception occurred in the API"
    data: dict = None

    def __init__(
        self,
        message: str = "The requested operation failed",
        debug: str = "An unknown and unhandled exception occurred in the API",
        data: dict = None,
        status: int = 500,
    ):
        self.status = status
        self.type = self.__class__.__name__
        self.message = message
        self.debug = debug
        self.data = data

    def dict(self):
        return {
            "status": self.status,
            "type": self.type,
            "message": self.message,
            "debug": self.debug,
            "data": self.data,
        }


TDependencyProtocol = NewType("TDependencyProtocol", Literal["dmss", "http"])


@dataclass(frozen=True)
class Dependency:
    """Class for any dependencies (external types) a entity references"""

    alias: str
    # Different ways we support to fetch dependencies.
    # dmss: Internally within the DMSS instance
    # http: A public HTTP GET call
    protocol: TDependencyProtocol
    address: str
    version: str = ""

    def __eq__(self, other):
        return (
            self.alias == other.alias
            and self.protocol == other.protocol
            and self.address == other.address
            and self.version == other.version
        )


def find_reference_schema(reference: str) -> Literal["dmss", "alias", "dotted", "package", "data_source"]:
    if "://" in reference:
        return "dmss"
    if ":" in reference:
        return "alias"
    if "." in reference:
        return "dotted"
    if reference[0] == "/":
        return "data_source"
    return "package"


def resolve_dependency(type_ref: str, dependencies: Dict[str, Dependency]) -> str:
    """Takes a type reference and dependencies. Returns the address for
    the Blueprint, prefixed with which protocol should be used to fetch it.
    Expected format is ALIAS:ADDRESS"""
    tag, path = type_ref.split(":", 1)
    path = path.strip(" /")
    dependency = dependencies.get(tag)
    if not dependency:
        raise ApplicationException(f"No dependency with alias '{tag}' was found in the entities dependencies list")
    address = dependency.address.strip(" /")

    if dependency.protocol == "dmss":
        return f"dmss://{address}/{path}"
    if dependency.protocol == "http":
        return f"http://{address}/{path}"

    raise ApplicationException(f"Protocol '{dependency.protocol}' is not a valid protocol for resolving dependencies")


def resolve_reference(reference: str, dependencies: Dict[str, Dependency], data_source: str, file_path: str) -> str:
    root_package = file_path.split("/", 1)[0]
    ref_schema = find_reference_schema(reference)

    if ref_schema == "dmss":
        return reference
    if ref_schema == "alias":
        return resolve_dependency(reference, dependencies)
    if ref_schema == "data_source":
        return f"dmss://{data_source}{reference}"
    if ref_schema == "package":
        return f"dmss://{data_source}/{root_package}/{reference}"
    if ref_schema in "dotted":
        normalized_dotted_ref: str = normpath(f"{file_path}/{reference}")
        return f"dmss://{data_source}/{normalized_dotted_ref}"

    raise ApplicationException(f"'{reference}' is not a valid reference for resolving dependencies")


def concat_dependencies(
    new_dependencies: List[dict], old_dependencies: Dict[str, Dependency], filename: str
) -> Dict[str, Dependency]:
    entity_dependencies = {v["alias"]: Dependency(**v) for v in new_dependencies}
    alias_intersect = entity_dependencies.keys() & old_dependencies.keys()

    # If there are duplicated aliases, raise error if they are not identical to the existing one
    for duplicated_alias in alias_intersect:
        if entity_dependencies[duplicated_alias] != old_dependencies[duplicated_alias]:
            raise ApplicationException(f"Conflicting dependency alias(es) in file '{filename}'. '{alias_intersect}'")
    old_dependencies.update(entity_dependencies)
    return old_dependencies


def unpack_and_save_zipfile(export_location: str, zip_file: ZipFile):
    """Unpack zipfile and save it to export_location. It is assumed that zip file only contains json files and folders.
    If file or folder to export already exists, an exception is raised.
    """
    zip_file_unpacked_path = f"{export_location}/{zip_file.filename.rstrip('.zip')}"

    zip_has_single_file_and_no_folders = (
        len(zip_file.filelist) == 1 and zip_file.filelist[0].filename.split("/")[0] == ""
    )
    if zip_has_single_file_and_no_folders:
        # If single file in the zip file (and the file is not inside a folder), the unpacked path has .json ending
        # (we assume the zip file always contains json files)
        zip_file_unpacked_path += ".json"

    if Path(zip_file_unpacked_path).exists():
        click.echo(emoji.emojize(f"\t:error: File or folder '{zip_file_unpacked_path}' already exists. Exiting."))
        raise ApplicationException("Path already exists")

    zip_file.extractall(path=export_location)
    click.echo(f"Saved unpacked zip file to '{zip_file_unpacked_path}'.")


def save_as_zip_file(export_location: str, filename: str, data: str):
    """Save binary data into a zip file on the local disk.
    If file or folder to export already exists, an exception is raised.
    """
    if not filename.endswith(".zip"):
        raise ApplicationException(message="file ending .zip must be included in filename!")
    saved_zip_file_path = f"{export_location}/{filename}"

    if Path(saved_zip_file_path).exists():
        click.echo(emoji.emojize(f"\t:error: File or folder '{saved_zip_file_path}' already exists. Exiting."))
        raise ApplicationException("Path already exists")

    with open(saved_zip_file_path, "wb") as file:
        file.write(data)
        click.echo(f"Wrote zip file to '{saved_zip_file_path}'")
