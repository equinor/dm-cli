import io
import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import Callable, Dict, List
from uuid import uuid4

from rich.console import Console
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from tqdm import tqdm

from .dmss import ApplicationException, dmss_api
from .dmss_api.exceptions import NotFoundException, ServiceException
from .domain import Dependency, File, Package
from .utils.reference import replace_relative_references
from .utils.resolve_local_ids import resolve_local_ids_in_document
from .utils.utils import concat_dependencies, replace_global_addresses

console = Console()

# Documents are posted in batches to avoid paying the per-request overhead for every document.
# Batching leaves little for a thread pool to overlap, and DMSS serves an import from a single
# worker, so uploading concurrently only made it contend with itself. Imports are sequential.
IMPORT_BATCH_SIZE = max(1, int(os.environ.get("DMSS_IMPORT_BATCH_SIZE", "100")))


def run_with_progress(description: str, items: list, task: Callable) -> None:
    """Run a task for every item, reporting progress as it goes."""
    if not items:
        return
    for item in tqdm(items, desc=description):
        task(item)


def _upload_documents(description: str, data_source: str, documents: List[dict]) -> None:
    """Upload documents as-is, in batches, falling back to one request per document on older DMSS versions."""
    if not documents:
        return
    batches = [documents[i : i + IMPORT_BATCH_SIZE] for i in range(0, len(documents), IMPORT_BATCH_SIZE)]
    uploaded = 0

    def upload_batch(batch: List[dict]) -> None:
        nonlocal uploaded
        dmss_api.document_add_simple_bulk(data_source, batch)
        uploaded += len(batch)

    try:
        run_with_progress(description, batches, upload_batch)
    except NotFoundException:
        if uploaded:
            # Earlier batches were accepted, so the endpoint does exist and this 404 is about the
            # documents rather than the route. Retrying as single uploads would duplicate them.
            raise
        # DMSS does not know the bulk endpoint, so upload one document at a time instead.
        run_with_progress(description, documents, lambda document: dmss_api.document_add_simple(data_source, document))


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
        dmss_api.document_add_simple(data_source, package.to_dict())
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
    retry=retry_if_exception_type(ServiceException),
)
def import_package_content(package: Package, data_source: str, destination: str, resolve_local_ids: bool) -> None:
    files: List[File] = []
    entities: List[dict] = []
    package.traverse_documents(
        lambda document, **kwargs: files.append(document) if isinstance(document, File) else entities.append(document)
    )
    uploaded_file_ids = {}
    if len(files) > 0:

        def upload_file(file: File) -> None:
            # The client takes the uploaded name from a (name, content) tuple, and DMSS splits that
            # name into the stored document's 'name' and 'filetype'.
            content = (os.path.basename(file.content.name), file.content.getvalue())
            dmss_api.file_upload(data_source, json.dumps({"file_id": file.uid}), content)
            uploaded_file_ids[f"dmss:/{file.content.destination}/{file.path.stem}"] = file.uid

        run_with_progress("  Adding files", files, upload_file)

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
            dmss_api.blob_upload(data_source, global_id, (os.path.basename(file_like.name), file_like.getvalue()))
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

        def prepare_entity(entity: dict) -> dict:
            document = replace_global_addresses(entity, destination, uploaded_file_ids, upload_global_file)
            if resolve_local_ids:
                name = f"/{document.get('name')}" if document.get("name") else f" of type {document.get('type')}"
                document = resolve_local_ids_in_document(document)
                print(f"Successfully resolved local IDs in:\t{destination}{name}")
            return document

        prepared_entities: List[dict] = []
        run_with_progress(
            "  Preparing entities", entities, lambda entity: prepared_entities.append(prepare_entity(entity))
        )
        _upload_documents("  Adding entities", data_source, prepared_entities)

    packages: List[Package] = []
    package.traverse_package(lambda package: packages.append(package))
    _upload_documents("  Adding packages", data_source, [p.to_dict() for p in packages])
