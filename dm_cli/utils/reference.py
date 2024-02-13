from os.path import normpath
from pathlib import Path
from typing import Dict, List, Union

from ..dmss import ApplicationException
from ..domain import Dependency
from ..enums import SIMOS, BuiltinDataTypes, ReferenceTypes
from .utils import Package, resolve_dependency


def resolve_reference(
    reference: str, dependencies: Dict[str, Dependency], destination: str, file_path: str | None
) -> str:
    destination = destination.rstrip("/")
    root_package = file_path.split("/", 1)[0] if file_path else ""
    try:
        if "://" in reference or reference == "_default_" or reference[0] == "^" or reference[0] == "~":
            return reference
        if ":" in reference:
            return resolve_dependency(reference, dependencies)
        if reference[0] == ".":
            normalized_dotted_ref: str = normpath(f"{file_path}/{reference}")
            return f"dmss://{destination}/{normalized_dotted_ref}"
        if reference[0] == "/":
            data_source = destination.split("/")[0]
            return f"dmss://{data_source}{reference}"
        return f"dmss://{destination}/{root_package}/{reference}"
    except ApplicationException as ex:
        ex.debug = f"File: {file_path}, Destination: {destination}, Root: {root_package}"
        raise ex


def resolve_storage_reference(address: str, source_path: Path):
    """
    Resolve the address into a file path that should points to a file on disk.

    @param address: The address to be resolved that points to a file on disk
    @param source_path: The source path app_data_dir_name/data_source_name/root_package_name
    """

    # Remove last item in source path to get to the data source directory
    source_path_items = str(source_path).split("/")[:-1]
    app_data_folder = "/".join(source_path_items)

    if address[0] == ".":
        raise ApplicationException("Relative references by . are not supported")

    return f"{app_data_folder}/{address}"


def replace_relative_references_in_package_meta(
    package: Package, dependencies: Dict[str, Dependency], data_source_id: str
) -> Package:
    """
    Replace relative references in meta attribute of the package and subpackages inside the package's content list.
    Recursively dig down into the package structure and replace the references inside the meta attribute of the package.
    """

    package.meta = replace_relative_references(
        "_meta_", package.meta, dependencies, data_source_id, file_path=package.path()
    )

    for document in package.content:
        if type(document) == Package:
            replace_relative_references_in_package_meta(document, dependencies, data_source_id)

    return package


def replace_relative_references(
    # shared arguments
    key: str,
    value,
    dependencies: Dict[str, Dependency],
    destination: str,
    file_path: Union[str, None] = None,
    zip_file: Union[str, None] = None,
    source_path: Path = None,
) -> Union[str, List[str], dict]:
    """
    Takes a key-value pair and returns the passed value, with
    relative references replaced with absolute ones.

    For Blob-entities; insert the binary data from the file into the entity.
    It digs down on complex types

    @param key: Name of the attribute being checked in the document
    @param value: Value of the attribute being checked in the document
    @param dependencies: A dict containing the dependencies of the document
    @param destination: The name of the data source where the document should be stored
    @param file_path: The path to the directory containing the documents

    When importing entities, the following additional parameter is required:
    @param parent_directory: When importing entities; the path to the directory from which relative paths to other blobs and documents are resolved

    When importing packages, the following additional parameter is required:
    @param zip_file:
    @param source_path: path to the root folder
    """

    KEYS_TO_CHECK = (
        "type",
        "attributeType",
        "extends",
        "_blueprintPath_",
        "address",
        "enumType",
    )  # These keys may contain a reference

    if (
        value == BuiltinDataTypes.OBJECT.value
        or value == BuiltinDataTypes.BINARY.value
        or value == BuiltinDataTypes.ANY.value
    ):
        return value

    if key in KEYS_TO_CHECK:
        if key == "extends":  # 'extends' is a list
            extends_list = []
            for blueprint in value:
                extends_list.append(
                    resolve_reference(
                        blueprint,
                        dependencies,
                        destination,
                        file_path,
                    )
                )
            return extends_list
        if key == "attributeType" and value in [data_type.value for data_type in BuiltinDataTypes]:
            return value
        return resolve_reference(
            value,
            dependencies,
            destination,
            file_path,
        )

    # If the value is a complex type, dig down recursively.
    if isinstance(value, dict) and value != {}:
        if not value.get("type"):
            raise KeyError(f"Object with key '{key}' is missing the required 'type' attribute. File: '{file_path}'")

        if (
            value.get("type") == BuiltinDataTypes.OBJECT.value
            or value.get("type") == BuiltinDataTypes.BINARY.value
            or value.get("type") == BuiltinDataTypes.ANY.value
        ):
            return value

        resolved_type = resolve_reference(
            value["type"],
            dependencies,
            destination,
            file_path,
        )

        # Do nothing with the address for references of type storage
        if resolved_type == SIMOS.REFERENCE.value and value.get("referenceType") == ReferenceTypes.STORAGE.value:
            resolved_path = resolve_storage_reference(value["address"], source_path)
            return {"type": SIMOS.REFERENCE.value, "address": f"{resolved_path}", "referenceType": "storage"}

        ignore_attributes = []
        if resolved_type == SIMOS.DEPENDENCY.value:
            ignore_attributes.append("address")

        return {
            k: replace_relative_references(
                k, v, dependencies, destination, file_path=file_path, zip_file=zip_file, source_path=source_path
            )
            if k not in ignore_attributes
            else v
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [
            replace_relative_references(
                key, v, dependencies, destination, file_path=file_path, zip_file=zip_file, source_path=source_path
            )
            for v in value
        ]

    # This means it's a primitive type or an absolute path, return as-is
    return value
