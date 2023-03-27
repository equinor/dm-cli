import json
from pathlib import Path
from typing import List
from uuid import uuid4

from progress.bar import IncrementalBar

from .dmss import dmss_api
from .domain import Package
from .utils.utils import upload_blobs_in_document


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


def import_package_tree(package: Package, destination: str) -> None:
    destination_parts = destination.split("/")
    data_source = destination_parts[0]

    documents_to_upload: List[dict] = []
    if len(destination_parts) == 1:  # We're importing a root package
        documents_to_upload.append(package.to_dict())
    else:  # We're importing a sub folder
        dmss_api.document_add_to_path(
            destination,
            json.dumps(package.to_dict()),
            update_uncontained=False,
            files=[],
        )

    package.traverse_documents(lambda document, **kwargs: documents_to_upload.append(document))
    package.traverse_package(lambda package: documents_to_upload.append(package.to_dict()))

    with IncrementalBar(
        f"\tImporting {package.name}",
        max=len(documents_to_upload),
        suffix="%(percent).0f%% - [%(eta)ds/%(elapsed)ds]",
    ) as bar:
        for document in documents_to_upload:
            document = upload_blobs_in_document(document, data_source)
            dmss_api.document_add_simple(data_source, document)
        bar.next()
