import io
import json
import pprint
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List
from uuid import uuid4

import click

from .dmss import ApplicationException, dmss_api
from .dmss_api.exceptions import ApiException, NotFoundException
from .domain import Dependency, Package
from .enums import SIMOS


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
        str(path.parent),
        json.dumps(package.to_dict()),
        update_uncontained=False,
        files=[],
    )


def dmss_exception_wrapper(function: Callable, *args, **kwargs) -> Any:
    try:
        return function(*args, **kwargs)
    except ApiException as e:
        exception = json.loads(e.body)
        click.echo(f"\nERROR: {exception['type']}")
        click.echo(f"\n\t{pprint.pprint(exception)}")
        exit(1)
    except (ApplicationException, NotFoundException) as error:
        click.echo(f"\nERROR: {error.type}")
        click.echo(f"\n\t{pprint.pprint(error)}")
        exit(1)
    except Exception as error:
        traceback.print_exc()
        click.echo(f"\nERROR: {error}")
        exit(1)
