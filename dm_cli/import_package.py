from pathlib import Path
from typing import List
from uuid import uuid4

from progress.bar import IncrementalBar

from .dmss import dmss_api
from .domain import Package
from .utils import upload_blobs_in_document


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
