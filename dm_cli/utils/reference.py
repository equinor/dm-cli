from os.path import normpath
from pathlib import Path
from typing import Dict, List, Union

from ..domain import Dependency
from ..enums import SIMOS, BuiltinDataTypes
from .utils import Package, resolve_dependency


def resolve_reference(reference: str, dependencies: Dict[str, Dependency], data_source: str, file_path: str) -> str:
    root_package = file_path.split("/", 1)[0]

    if "://" in reference or reference == "_default_" or reference[0] == "^":
        return reference
    if ":" in reference:
        return resolve_dependency(reference, dependencies)
    if reference[0] == ".":
        normalized_dotted_ref: str = normpath(f"{file_path}/{reference}")
        return f"dmss://{data_source}/{normalized_dotted_ref}"
    if reference[0] == "/":
        return f"dmss://{data_source}{reference}"
    return f"dmss://{data_source}/{root_package}/{reference}"


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
