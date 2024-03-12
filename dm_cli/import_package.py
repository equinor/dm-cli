import io
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, List
from uuid import uuid4

from rich.console import Console
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from tqdm import tqdm

from .dmss import ApplicationException, dmss_api
from .domain import Dependency, File, Package
from .utils.reference import replace_relative_references
from .utils.resolve_local_ids import resolve_local_ids_in_document
from .utils.utils import concat_dependencies, replace_global_addresses

console = Console()


def add_object_to_package(path: Path, package: Package, object: io.BytesIO) -> None:
    if len(path.parts) == 1:  # End of path means the actual document
        file = File(
            uid=str(uuid4()),  # This UID will be the data source ID for this file
            name=object.name,
            content=object,
            path=path,
        )
        package.content.append(file)
        return
    items = [item for item in package.content if not isinstance(item, File)]
    sub_folder = next((p for p in items if p["name"] == path.parts[0]), None)
    if not sub_folder:  # If the sub folder has not already been created on parent, create it
        sub_folder = Package(name=path.parts[0], parent=package)
        package.content.append(sub_folder)

    new_path = str(path).split("/", 1)[1]  # Remove first element in path before stepping down
    return add_object_to_package(Path(new_path), sub_folder, object)


def add_file_to_package(path: Path, package: Package, document: dict) -> None:
    if len(path.parts) == 1:  # End of path means the actual document
        if path.name.endswith("package.json"):
            # if document is a package.json file, add meta info to package instead of adding it to content list.
            package.meta = document.get("_meta_", {})
            return
        # Create a UUID if the document does not have one
        package.content.append({**document, "_id": document.get("_id", str(uuid4()))})
        return
    items = [item for item in package.content if not isinstance(item, File)]
    sub_folder = next((p for p in items if p["name"] == path.parts[0]), None)
    if not sub_folder:  # If the sub folder has not already been created on parent, create it
        sub_folder = Package(name=path.parts[0], parent=package)
        package.content.append(sub_folder)

    new_path = str(path).split("/", 1)[1]  # Remove first element in path before stepping down
    return add_file_to_package(Path(new_path), sub_folder, document)


def add_package_to_package(path: Path, package: Package) -> None:
    if len(path.parts) == 1:
        package.content.append(Package(name=path.parts[0], parent=package))
        return
    items = [item for item in package.content if not isinstance(item, File)]
    sub_folder = next((p for p in items if p["name"] == path.parts[0]), None)
    if not sub_folder:  # If the sub folder has not already been created on parent, create it
        sub_folder = Package(name=path.parts[0], parent=package)
        package.content.append(sub_folder)

    new_path = str(path).split("/", 1)[1]  # Remove first element in path before stepping down
    return add_package_to_package(Path(new_path), sub_folder)


def import_package_tree(package: Package, destination: str, raw_package_import: bool, resolve_local_ids: bool) -> None:
    destination_parts = destination.split("/")
    data_source = destination_parts[0]

    if raw_package_import:
        dmss_api.document_add_simple(data_source, body=package.to_dict())
    else:
        dmss_api.document_add(
            destination,
            json.dumps(package.to_dict()),
            files=[],
        )

    import_package_content(package, data_source, destination, resolve_local_ids)


@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    retry=retry_if_not_exception_type(ApplicationException),
)
def import_package_content(package: Package, data_source: str, destination: str, resolve_local_ids: bool) -> None:
    files: List[File] = []
    entities: List[dict] = []
    package.traverse_documents(
        lambda document, **kwargs: files.append(document) if isinstance(document, File) else entities.append(document)
    )
    uploaded_file_ids = {}
    if len(files) > 0:
        with tqdm(files, desc=f"  Adding files") as bar:
            for file in files:
                dmss_api.file_upload(data_source, json.dumps({"file_id": file.uid}), file.content)
                uploaded_file_ids[f"dmss:/{file.content.destination}/{file.path.stem}"] = file.uid
                bar.update()

    def upload_global_file(address: str) -> str:
        """Handling uploading of global files."""
        filepath = Path(address)
        if not filepath.is_file():
            raise ApplicationException(
                f"Tried to upload file with address '{address}'. The file was not found", data=package.to_dict()
            )
        if filepath.suffix != ".json":
            # Binary files
            with open(address, "rb") as f:
                file_like = io.BytesIO(f.read())
            file_like.name = filepath.stem
            global_id = str(uuid4())
            dmss_api.blob_upload(data_source, global_id, file_like)
            return global_id
        else:
            try:
                with open(address) as f:
                    global_document = json.load(f)
                # Get dependencies from package
                dependencies: Dict[str, Dependency] = {
                    dependency["alias"]: Dependency(**dependency)
                    for dependency in package.meta.get("dependencies", [])
                }
                # Add dependencies from entity
                dependencies = concat_dependencies(
                    global_document.get("_meta_", {}).get("dependencies", []), dependencies, address
                )
                global_document = replace_relative_references(
                    global_document,
                    dependencies,
                    destination,
                    file_path=address,
                )
                global_id = dmss_api.document_add_simple(data_source, global_document)
                return global_id
            except JSONDecodeError:
                raise Exception(f"Failed to load the file '{address}' as a JSON document")

    if len(entities) > 0:
        with tqdm(entities, desc=f"  Adding entities") as bar:
            for entity in entities:
                document = replace_global_addresses(entity, destination, uploaded_file_ids, upload_global_file)
                if resolve_local_ids:
                    name = f"/{document.get('name')}" if document.get("name") else f" of type {document.get('type')}"
                    document = resolve_local_ids_in_document(document)
                    print(f"Successfully resolved local IDs in:\t{destination}{name}")
                dmss_api.document_add_simple(data_source, document)
                bar.update()

    packages: List[Package] = []
    package.traverse_package(lambda package: packages.append(package))
    if len(packages) > 0:
        with tqdm(packages, desc=f"  Adding packages") as bar:
            for package in packages:
                dmss_api.document_add_simple(data_source, package.to_dict())
                bar.update()
