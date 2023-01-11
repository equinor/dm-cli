import io
import json
from os.path import normpath
from pathlib import Path
from typing import Dict, List, Literal, Union
from uuid import uuid4
from zipfile import ZipFile

import click
import emoji

from .dmss import ApplicationException, dmss_api
from .dmss_api.exceptions import ApiException
from .domain import Dependency
from .enums import SIMOS, BuiltinDataTypes


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


def document_already_exists(api_exception: ApiException) -> bool:
    error = json.loads(api_exception.body)
    if error.get("type") == "BadRequestException" and "already exists" in error.get("message"):
        print(f"ERROR: {error.get('message')}")
        return True
    return False


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

    # If the value is a complex type, dig down recursively. Ignore the _meta_ key
    if key != "_meta_" and isinstance(value, dict) and value != {}:
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


def upload_blobs_in_document(document: dict, data_source_id: str) -> dict:
    """
    Uploads any 'system/SIMOS/Blob' types in the document, and replaces the data with UUIDs
    """
    try:
        if document["type"] == SIMOS.BLOB.value:
            blob_id = document.get("_blob_id", str(uuid4()))
            blob_name = Path(document["name"]).stem
            file_like = io.BytesIO(document["_blob_data_"])
            file_like.name = blob_name
            res = dmss_api.blob_upload(data_source_id, blob_id, file_like)
            return {
                "name": blob_name,
                "type": SIMOS.BLOB.value,
                "_blob_id": blob_id,
                "size": len(document["_blob_data_"]),
            }
    except KeyError as error:
        reduced_document = {k: v for k, v in document.items() if isinstance(v, str)}
        raise KeyError(f"The document; '{reduced_document}' is missing a required attribute: {error}")
    except ApiException as api_exception:
        if document_already_exists(api_exception):
            return {
                "name": blob_name,
                "type": SIMOS.BLOB.value,
                "_blob_id": blob_id,
                "size": len(document["_blob_data_"]),
            }
        raise

    for key, value in document.items():
        if key == "_meta_":  # meta data can never contain blob data.
            return document
        if isinstance(value, dict) and value:
            document[key] = upload_blobs_in_document(value, data_source_id)
        if isinstance(value, list) and value:
            if len(value) > 0 and isinstance(value[0], dict):
                document[key] = [upload_blobs_in_document(item, data_source_id) for item in document[key]]

    return document
