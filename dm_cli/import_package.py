import io
import json
from pathlib import Path
from typing import List, Union
from uuid import uuid4

import typer
from rich.console import Console
from rich.text import Text
from tqdm import tqdm

from dm_cli.state import state

from .dmss import dmss_api
from .domain import Entity, File, Package
from .utils.resolve_local_ids import resolve_local_ids_in_document
from .utils.utils import replace_file_addresses

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
            package.meta = document["_meta_"]
            return
        # Create a UUID if the document does not have one
        uid = document.get("_id", str(uuid4()))
        entity = Entity(
            name=document.get("name", ""),
            content={**document, "_id": uid},
            filename=str(path),
            directory=f"{package.path()}",
        )
        package.content.append(entity)
        return
    items = [item for item in package.content if not isinstance(item, Entity)]
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


def import_package_tree(
    package: Package, destination: str, global_ids: dict, raw_package_import: bool, resolve_local_ids: bool
) -> None:
    destination_parts = destination.split("/")
    data_source = destination_parts[0]

    if raw_package_import:
        dmss_api.document_add_simple(data_source, body=package.to_dict())
    else:
        dmss_api.document_add(
            destination,
            json.dumps(package.to_dict()),
            update_uncontained=False,
            files=[],
        )

    data_source = destination_parts[0]
    import_package_content(package, data_source, global_ids, resolve_local_ids)


def import_package_content(package: Package, data_source: str, global_ids: dict, resolve_local_ids: bool) -> dict:
    files: List[File] = []
    entities: List[Entity] = []
    package.traverse_documents(
        lambda document, **kwargs: files.append(document) if isinstance(document, File) else entities.append(document)
    )
    uploaded_file_ids = {}
    if len(files) > 0:
        with tqdm(files, desc=f"  Adding files") as bar:
            for file in files:
                try:
                    dmss_api.file_upload(data_source, json.dumps({"file_id": file.uid}), file.content)
                    uploaded_file_ids[f"dmss:/{file.content.destination}/{file.path.stem}"] = file.uid
                except Exception as error:
                    if state.debug:
                        console.print_exception()
                    text = Text(str(error))
                    console.print(text, style="red1")
                    raise typer.Exit(code=1)
                bar.update()

    uploaded_entity_ids = {}
    if len(entities) > 0:
        with tqdm(entities, desc=f"  Adding entities") as bar:
            for entity in entities:
                try:
                    document = replace_file_addresses(entity.content, data_source, uploaded_file_ids, global_ids)
                    if resolve_local_ids:
                        name = (
                            f"/{document.get('name')}" if document.get("name") else f" of type {document.get('type')}"
                        )
                        document = resolve_local_ids_in_document(document)
                        print(f"Successfully resolved local IDs in:\t{data_source}{name}")
                    document_id = dmss_api.document_add_simple(data_source, document)
                    uploaded_entity_ids[f"dmss://{data_source}/{entity.directory}/{entity.filename}"] = document_id
                except Exception as error:
                    if state.debug:
                        console.print_exception()
                    text = Text(str(error))
                    console.print(text, style="red1")
                    raise typer.Exit(code=1)
                bar.update()

    packages: List[Package] = []
    package.traverse_package(lambda package: packages.append(package))
    if len(packages) > 0:
        with tqdm(packages, desc=f"  Adding packages") as bar:
            for package in packages:
                try:
                    dmss_api.document_add_simple(data_source, package.to_dict())
                except Exception as error:
                    if state.debug:
                        console.print_exception()
                    text = Text(str(error))
                    console.print(text, style="red1")
                    raise typer.Exit(code=1)
                bar.update()

    return uploaded_entity_ids
