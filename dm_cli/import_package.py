import io
from pathlib import Path
from typing import Dict, List, Union
from uuid import uuid4
from zipfile import ZipFile

from progress.bar import IncrementalBar

from .dmss import dmss_api
from .domain import Package
from .enums import PRIMITIVES, SIMOS
from .utils import Dependency, resolve_reference

keys_to_check = ("type", "attributeType", "extends", "_blueprintPath_")  # These keys may contain a reference


def replace_relative_references(
    key: str,
    value,
    dependencies: Dict[str, Dependency],
    data_source: str,
    zip_file: ZipFile = None,
    file_path: str = None,
) -> Union[str, List[str], dict]:
    """
    Takes a key-value pair, along with some context, and returns the passed value, with
    relative references updated with absolute ones.

    For Blob-entities. Insert the binary data from the file into the entity.
    It digs down on complex types.
    """

    if key in keys_to_check:
        if key == "extends":  # 'extends' is a list
            extends_list = []
            for i, blueprint in enumerate(value):
                extends_list.append(resolve_reference(blueprint, dependencies, data_source, file_path))
            return extends_list
        if key == "attributeType" and value in PRIMITIVES:
            return value
        return resolve_reference(
            value,
            dependencies,
            data_source,
            file_path,
        )

    # If the value is a complex type, dig down recursively. Ignore the _meta_ key.
    if key != "_meta_" and isinstance(value, dict) and value != {}:
        # First check if the type is a blob type
        if (
            replace_relative_references("type", value["type"], dependencies, data_source, zip_file, file_path)
            == SIMOS.BLOB.value
        ):
            # Add blob data to the blob-entity
            if value["name"][0] == "/":  # It's a relative reference to the blob file. Get root_package_name...
                root_package_name = f"{zip_file.filelist[0].filename.split('/', 1)[0]}"
                # '_blob_data' is a temporary key for keeping the binary data
                return {
                    "_blob_data_": zip_file.read(f"{root_package_name}{value['name']}"),
                    **value,
                    "type": SIMOS.BLOB.value,
                }

            return {"_blob_data_": zip_file.read(value["name"]), **value}

        return {
            k: replace_relative_references(k, v, dependencies, data_source, zip_file, file_path)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [replace_relative_references(key, v, dependencies, data_source, zip_file, file_path) for v in value]

    # This means it's a primitive type or an absolute path, return it as is
    return value


def add_file_to_package(path: Path, package: Package, document: dict) -> None:
    if len(path.parts) == 1:  # End of path means the actual document
        if path.name.endswith("package.json"):
            # if document is a package.json file, add meta info to package instead of adding it to content list.
            package.meta = document["_meta_"]
            return
        # Create a UUID if the document does not have one
        package.content.append({**document, "_id": document.get("_id", str(uuid4()))})
        return
    sub_folder = next((p for p in package.content if p["name"] == path.parts[0]), None)
    if not sub_folder:  # If the sub folder has not already been created on parent, create it
        sub_folder = Package(name=path.parts[0], parent=package)
        package.content.append(sub_folder)

    new_path = str(path).split("/", 1)[1]  # Remove first element in path before stepping down
    return add_file_to_package(Path(new_path), sub_folder, document)


def add_package_to_package(path: Path, package: Package) -> None:
    if len(path.parts) == 1:
        package.content.append(Package(name=path.parts[0], parent=package))
        return

    sub_folder = next((p for p in package.content if p["name"] == path.parts[0]), None)
    if not sub_folder:  # If the sub folder has not already been created on parent, create it
        sub_folder = Package(name=path.parts[0], parent=package)
        package.content.append(sub_folder)

    new_path = str(path).split("/", 1)[1]  # Remove first element in path before stepping down
    return add_package_to_package(Path(new_path), sub_folder)


def upload_blobs_in_document(document: dict, data_source_id: str) -> dict:
    """Uploads any 'system/SIMOS/Blob' types in the document, and replaces the data with created uuid's."""
    try:
        if document["type"] == SIMOS.BLOB.value:
            blob_id = document.get("_blob_id", str(uuid4()))
            blob_name = Path(document["name"]).stem
            file_like = io.BytesIO(document["_blob_data_"])
            file_like.name = blob_name
            dmss_api.blob_upload(data_source_id, blob_id, file_like)
            return {
                "name": blob_name,
                "type": SIMOS.BLOB.value,
                "_blob_id": blob_id,
                "size": len(document["_blob_data_"]),
            }
    except KeyError as error:
        reduced_document = {k: v for k, v in document.items() if isinstance(v, str)}
        raise KeyError(f"The document; '{reduced_document}' is missing a required attribute: {error}")
    for key, value in document.items():
        if key == "_meta_":  # meta data can never contain blob data. Skip for performance
            return document
        if isinstance(value, dict) and value:
            document[key] = upload_blobs_in_document(value, data_source_id)
        if isinstance(value, list) and value:
            if len(value) > 0 and isinstance(value[0], dict):
                document[key] = [upload_blobs_in_document(item, data_source_id) for item in document[key]]
    return document


def import_package_tree(root_package: Package, data_source_id: str) -> None:
    documents_to_upload: List[dict] = [root_package.to_dict()]
    root_package.traverse_documents(lambda document, **kwargs: documents_to_upload.append(document))
    root_package.traverse_package(lambda package: documents_to_upload.append(package.to_dict()))

    with IncrementalBar(
        f"\tImporting {root_package.name}",
        max=len(documents_to_upload),
        suffix="%(percent).0f%% - [%(eta)ds/%(elapsed)ds]",
    ) as bar:
        for document in documents_to_upload:
            document = upload_blobs_in_document(document, data_source_id)
            dmss_api.document_add_simple(data_source_id, document)
        bar.next()
