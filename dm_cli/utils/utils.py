import io
import json
import pprint
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

import typer
from rich import print
from rich.console import Console

from dm_cli.dmss import ApplicationException, dmss_api
from dm_cli.dmss_api.exceptions import ApiException, NotFoundException

from ..domain import Dependency, Package
from ..enums import SIMOS

console = Console()


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


def add_package_to_path(name: str, path: Path):
    package = Package(name, is_root=len(path.parts) == 2)
    dmss_api.document_add_to_path(
        f"/{str(path.parent)}/",
        json.dumps(package.to_dict()),
        update_uncontained=False,
        files=[],
    )


def destination_is_root(destination: Path) -> bool:
    if len(destination.parts) > 1:
        return False
    return True


def ensure_package_structure(path: Path):
    """Create any missing packages in the provided path (mkdir -R)"""
    try:
        dmss_api.document_get(f"dmss://{path}/")
    except NotFoundException as e:
        error = json.loads(e.body)
        if error["status"] != 404:
            print(f"Target package '{path}' is likely corrupt!")
            pprint.pformat(error)
            raise typer.Exit(code=1)

        if len(path.parts) > 2:  # We're at root package level. Do not check for datasource.
            ensure_package_structure(path.parent)

        add_package_to_path(path.name, path)
        print(f"Target folder '{path.name}' was missing in '{path.parent}'. Created: ✓")
