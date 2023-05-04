import io
import json
from pathlib import Path
from typing import List
from uuid import uuid4

import typer
from progress.bar import IncrementalBar
from rich.console import Console
from rich.text import Text

from dm_cli.state import state

from .dmss import dmss_api
from .domain import File, Package
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


def import_package_tree(package: Package, destination: str) -> None:
    destination_parts = destination.split("/")
    data_source = destination_parts[0]

    if len(destination_parts) == 1:  # We're importing a root package
        dmss_api.document_add(
            destination,
            json.dumps(package.to_dict()),
            update_uncontained=False,
            files=[],
        )
    else:  # We're importing a sub folder
        dmss_api.document_add(
            destination,
            json.dumps(package.to_dict()),
            update_uncontained=False,
            files=[],
        )

    documents_to_upload: List[dict] = []
    package.traverse_documents(lambda document, **kwargs: documents_to_upload.append(document))
    package.traverse_package(lambda package: documents_to_upload.append(package.to_dict()))

    files_to_upload = {}
    with IncrementalBar(
        f"\tImporting documents of type 'File' from {package.name}",
        max=len(documents_to_upload),
        suffix="%(percent).0f%% - [%(eta)ds/%(elapsed)ds]",
    ) as bar:
        for document in documents_to_upload:
            if isinstance(document, File):
                try:
                    dmss_api.file_upload(data_source, json.dumps({"file_id": document.uid}), document.content)
                    files_to_upload[f"dmss:/{document.content.destination}/{document.path.stem}"] = document.uid
                except Exception as error:
                    if state.debug:
                        console.print_exception()
                    text = Text(str(error))
                    console.print(text, style="red1")
                    raise typer.Exit(code=1)
        bar.next()

    with IncrementalBar(
        f"\tImporting {package.name}",
        max=len(documents_to_upload),
        suffix="%(percent).0f%% - [%(eta)ds/%(elapsed)ds]",
    ) as bar:
        for document in documents_to_upload:
            if not isinstance(document, File):
                document = replace_file_addresses(document, data_source, files_to_upload)
                try:
                    dmss_api.document_add_simple(data_source, document)
                except Exception as error:
                    if state.debug:
                        console.print_exception()
                    text = Text(str(error))
                    console.print(text, style="red1")
                    raise typer.Exit(code=1)
        bar.next()
