import io
import json
from json import JSONDecodeError
from pathlib import Path
from zipfile import ZipFile

from rich import print
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .dmss import ApplicationException, dmss_api
from .dmss_api.exceptions import NotFoundException
from .import_package import import_package_tree
from .package_tree_from_zip import package_tree_from_zip
from .state import state
from .utils.reference import replace_relative_references
from .utils.utils import (
    concat_dependencies,
    console,
    destination_is_root,
    ensure_package_structure,
)
from .utils.zip import zip_all


@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    retry=retry_if_not_exception_type(ApplicationException),
)
def import_document(source_path: Path, destination: str, document: dict):
    remote_dependencies = dmss_api.export_meta(destination)
    old_dependencies = {dependency["alias"]: dependency for dependency in remote_dependencies.get("dependencies", [])}

    dependencies = concat_dependencies(
        new_dependencies=document.get("_meta_", {}).get("dependencies", []),
        old_dependencies=old_dependencies,
        filename=source_path.name,
    )

    # Replace references
    prepared_document = replace_relative_references(document, dependencies, destination)

    document_json_str = json.dumps(prepared_document)
    dmss_api.document_add(
        destination,
        document_json_str,
        files=[],
    )


def import_single_entity(source_path: Path, destination: str):
    ensure_package_structure(Path(destination))
    print(f"Importing ENTITY '{source_path.name}' --> '{destination}'")

    try:  # Load the JSON document
        with open(source_path, "r") as fh:
            if Path(source_path).suffix == ".json":
                import_document(source_path, destination, json.load(fh))
            else:
                print(f"Unsupported file type {source_path}")
    except JSONDecodeError:
        raise Exception(f"Failed to load the file '{source_path.name}' as a JSON document")


def remove_by_path_ignore_404(target: str):
    try:
        dmss_api.document_remove(target)
    except NotFoundException:
        pass


@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    retry=retry_if_not_exception_type(ApplicationException),
)
def import_folder_entity(
    source_path: Path,
    destination: str,
    raw_package_import: bool = False,
    resolve_local_ids: bool = False,
) -> dict:
    destination_path = Path(destination)

    # Check if target already exists on remote. Then delete or raise exception
    target = f"{destination}/{source_path.name}"
    exists = dmss_api.document_check(target)
    if exists:
        if not state.force:
            raise ValueError(f"Failed to upload to '{target}' - It already exists.")
        console.print(f"'{target}' already exists.  Replacing it...", style="dark_orange")
        dmss_api.document_remove(target)

    dependencies = {}
    is_root = destination_is_root(destination_path)
    if not is_root:
        ensure_package_structure(destination_path)
        remote_dependencies = dmss_api.export_meta(f"{destination}")
        dependencies = {dependency["alias"]: dependency for dependency in remote_dependencies.get("dependencies", [])}

    memory_file = io.BytesIO()
    with ZipFile(memory_file, mode="w") as zip_file:
        zip_all(
            zip_file,
            source_path,
            write_folder=True,
        )
    memory_file.seek(0)

    package = package_tree_from_zip(
        destination, memory_file, is_root=is_root, extra_dependencies=dependencies, source_path=source_path
    )
    import_package_tree(package, destination, raw_package_import, resolve_local_ids)
