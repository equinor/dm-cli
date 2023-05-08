import io
import json
from json import JSONDecodeError
from pathlib import Path
from zipfile import ZipFile

from rich import print

from .dmss import dmss_api
from .dmss_api.exceptions import NotFoundException
from .domain import Dependency
from .import_package import import_package_tree
from .package_tree_from_zip import package_tree_from_zip
from .state import state
from .utils.reference import replace_relative_references
from .utils.utils import (
    concat_dependencies,
    console,
    destination_is_root,
    ensure_package_structure,
    upload_blobs_in_document,
)
from .utils.zip import zip_all


def import_single_entity(source_path: Path, destination: str):
    ensure_package_structure(Path(destination))
    print(f"Importing ENTITY '{source_path.name}' --> '{destination}'")
    data_source_id, package = destination.split("/", 1)

    try:  # Load the JSON document
        with open(source_path, "r") as fh:
            document = json.load(fh)
    except JSONDecodeError:
        raise Exception(f"Failed to load the file '{source_path.name}' as a JSON document")

    remote_dependencies = dmss_api.export_meta(f"{data_source_id}/{package}")
    old_dependencies = {v["alias"]: Dependency(**v) for v in remote_dependencies.get("dependencies", [])}

    dependencies = concat_dependencies(
        new_dependencies=document.get("_meta_", {}).get("dependencies", []),
        old_dependencies=old_dependencies,
        filename=source_path.name,
    )

    # Replace references
    prepared_document = {}
    for key, val in document.items():
        prepared_document[key] = replace_relative_references(
            key,
            val,
            dependencies,
            data_source_id,
            file_path=package,
            parent_directory=source_path.parent,
        )

    # Upload blobs
    prepared_document = upload_blobs_in_document(prepared_document, data_source_id)
    document_json_str = json.dumps(prepared_document)
    dmss_api.document_add_to_path(
        f"{destination}",
        document_json_str,
        update_uncontained=True,
        files=[],
    )


def import_folder_entity(source_path: Path, destination: str) -> None:
    print(f"Importing PACKAGE '{source_path.name}' --> '{destination}/'")
    destination_path = Path(destination)
    data_source = destination_path.parts[0]

    try:  # Check if target already exists on remote. Then delete or raise exception
        dmss_api.document_get(f"dmss://{destination}/{source_path.name}")
        if not state.force:
            raise ValueError(f"Failed to upload to 'dmss://{destination}/{source_path.name}' - It already exists.")
        console.print(
            f"WARNING: '{destination}/{source_path.name}' already exists. Replacing it...", style="dark_orange"
        )
        dmss_api.document_remove_by_path(f"{destination}/{source_path.name}")
    except NotFoundException:
        pass  # The folder we're trying to upload does not exist, which is fine

    dependencies = {}
    is_root = destination_is_root(destination_path)
    if not is_root:
        ensure_package_structure(destination_path)
        remote_dependencies = dmss_api.export_meta(f"{destination}")
        dependencies = {v["alias"]: Dependency(**v) for v in remote_dependencies.get("dependencies", [])}

    memory_file = io.BytesIO()
    with ZipFile(memory_file, mode="w") as zip_file:
        zip_all(
            zip_file,
            source_path,
            write_folder=True,
        )
    memory_file.seek(0)

    package = package_tree_from_zip(data_source, memory_file, is_root=is_root, extra_dependencies=dependencies)
    import_package_tree(package, destination)
