from os.path import normpath
from pathlib import Path
from typing import Dict, List, Literal, Union

from ..dmss import ApplicationException
from ..domain import Dependency
from ..enums import SIMOS, BuiltinDataTypes
from .utils import resolve_dependency


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


def resolve_reference(reference: str, dependencies: Dict[str, Dependency], data_source: str, file_path: str) -> str:
    root_package = file_path.split("/", 1)[0]
    ref_schema = find_reference_schema(reference)

    if ref_schema == "dmss" or reference == "_default_":
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


def replace_relative_references(
    # shared arguments
    key: str,
    value,
    dependencies: Dict[str, Dependency],
    data_source: str,
    file_path: Union[str, None] = None,
    # for entities
    parent_directory: Union[Path, None] = None,
    # for packages
    zip_file: Union[str, None] = None,
) -> Union[str, List[str], dict]:
    """
    Takes a key-value pair and returns the passed value, with
    relative references replaced with absolute ones.

    For Blob-entities; insert the binary data from the file into the entity.
    It digs down on complex types

    @param key: Name of the attribute being checked in the document
    @param value: Value of the attribute being checked in the document
    @param dependencies: A dict containing the dependencies of the document
    @param data_source: The name of the data source where the document should be stored
    @param file_path: The path to the directory containing the documents

    When importing entities, the following additional parameter is required:
    @param parent_directory: When importing entities; the path to the directory from which relative paths to other blobs and documents are resolved

    When importing packages, the following additional parameter is required:
    @param zip_file:
    """

    KEYS_TO_CHECK = (
        "type",
        "attributeType",
        "extends",
        "_blueprintPath_",
        "address",
    )  # These keys may contain a reference

    if value == BuiltinDataTypes.OBJECT.value or value == BuiltinDataTypes.BINARY.value:
        return value

    if key in KEYS_TO_CHECK:
        if key == "extends":  # 'extends' is a list
            extends_list = []
            for blueprint in value:
                extends_list.append(
                    resolve_reference(
                        blueprint,
                        dependencies,
                        data_source,
                        file_path,
                    )
                )
            return extends_list
        if key == "attributeType" and value in [data_type.value for data_type in BuiltinDataTypes]:
            return value
        return resolve_reference(
            value,
            dependencies,
            data_source,
            file_path,
        )

    # If the value is a complex type, dig down recursively.
    if isinstance(value, dict) and value != {}:
        if not value.get("type"):
            raise KeyError(f"Object with key '{key}' is missing the required 'type' attribute. File: '{file_path}'")

        if value.get("type") == BuiltinDataTypes.OBJECT.value or value.get("type") == BuiltinDataTypes.BINARY.value:
            return value

        resolved_type = resolve_reference(
            value["type"],
            dependencies,
            data_source,
            file_path,
        )

        ignore_attributes = []
        if resolved_type == SIMOS.DEPENDENCY.value:
            ignore_attributes.append("address")

        return {
            k: replace_relative_references(
                k,
                v,
                dependencies,
                data_source,
                file_path=file_path,
                zip_file=zip_file,
            )
            if k not in ignore_attributes
            else v
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [
            replace_relative_references(
                key,
                v,
                dependencies,
                data_source,
                file_path=file_path,
                zip_file=zip_file,
            )
            for v in value
        ]

    # This means it's a primitive type or an absolute path, return as-is
    return value
