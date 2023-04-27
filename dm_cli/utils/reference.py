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

    KEYS_TO_CHECK = ("type", "attributeType", "extends", "_blueprintPath_")  # These keys may contain a reference

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
        # First check if the type is a blob type
        if (
            replace_relative_references(
                "type",
                value["type"],
                dependencies,
                data_source,
                file_path=file_path,
                zip_file=zip_file,
            )
            == SIMOS.BLOB.value
        ):
            if not value.get("name"):
                raise KeyError(
                    f"Blob object with key '{key}' is missing the required 'name' attribute. File: '{file_path}'"
                )
            # Add blob data to the blob-entity
            if parent_directory:  # entity
                _blob_data = None
                # value['name'] must be relative to the parent directory of the document accessing it
                _blob_path = parent_directory.joinpath(value["name"])
                if not _blob_path.is_file():
                    raise FileNotFoundError(
                        f"Failed to load the blob file '{_blob_path}' (referenced in '{key}.{value}')"
                    )

                with open(_blob_path, "rb") as fh:
                    _blob_data = fh.read()

                return {
                    "_blob_data_": _blob_data,
                    **{
                        blob_key: blob_val
                        if blob_key in ["name", "_id", "_blob_id"]
                        else resolve_reference(blob_val, dependencies, data_source, file_path)
                        for blob_key, blob_val in value.items()
                    },
                }
            elif zip_file:  # package
                if value["name"][0] == "/":  # It's a relative reference to the blob file. Get root_package_name...
                    root_package_name = f"{zip_file.filelist[0].filename.split('/', 1)[0]}"
                    # '_blob_data_' is a temporary key for keeping the binary data
                    return {
                        "_blob_data_": zip_file.read(f"{root_package_name}{value['name']}"),
                        **value,
                        "type": SIMOS.BLOB.value,
                    }
                return {"_blob_data_": zip_file.read(value["name"]), **value}
            else:
                raise ValueError(
                    f"Missing required parameter: Either 'parent_directory' (entity) or 'zip_file' (package) must be provided."
                )

        return {
            k: replace_relative_references(
                k,
                v,
                dependencies,
                data_source,
                file_path=file_path,
                zip_file=zip_file,
            )
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
