import json
import os
import pprint
from pathlib import Path
from typing import Callable, Dict, List

import typer
from rich import print
from rich.console import Console

from dm_cli.dmss import ApplicationException, dmss_api
from dm_cli.dmss_api.exceptions import ApiException, NotFoundException
from dm_cli.utils.file_structure import get_app_dir_structure, get_json_files_in_dir

from ..domain import Dependency, Package
from ..enums import SIMOS

console = Console()


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
    entity_dependencies = {dependency["alias"]: Dependency(**dependency) for dependency in new_dependencies}
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


def add_package_to_path(name: str, path: Path):
    package = Package(name, is_root=len(path.parts) == 2)
    dmss_api.document_add(
        str(path.parent),
        json.dumps(package.to_dict()),
        files=[],
    )


def replace_global_addresses(
    document: dict, data_source_id: str, files_to_upload: dict, upload_global_file: Callable
) -> dict:
    # This is for contained Files(blob data)? If so they should be embedded in the json document, not uploaded as a blob
    if document["type"] == SIMOS.REFERENCE.value and document["address"] in files_to_upload:
        blob_id = files_to_upload[document["address"]]
        document["address"] = f"${blob_id}"
    # This is for model contained, storage-uncontained documents. They are stored on disk in the "global" folder
    if document["type"] == SIMOS.REFERENCE.value and document["referenceType"] == "storage":
        global_id = upload_global_file(document["address"])
        document["address"] = f"${global_id}"
    for key, value in document.items():
        if key == "_meta_":  # meta data can never contain blob data.
            return document
        if isinstance(value, dict) and value:
            document[key] = replace_global_addresses(value, data_source_id, files_to_upload, upload_global_file)
        if isinstance(value, list) and value:
            if len(value) > 0 and isinstance(value[0], dict):
                document[key] = [
                    replace_global_addresses(item, data_source_id, files_to_upload, upload_global_file)
                    for item in document[key]
                ]
    return document


def destination_is_root(destination: Path) -> bool:
    if len(destination.parts) > 1:
        return False
    return True


def ensure_package_structure(path: Path):
    """Create any missing packages in the provided path (mkdir -R)"""
    try:
        dmss_api.document_get(f"dmss://{path}/")
    except NotFoundException as e:
        error = json.loads(e.body)
        if error["status"] != 404:
            print(f"Target package '{path}' is likely corrupt!")
            pprint.pformat(error)
            raise typer.Exit(code=1)

        if len(path.parts) > 2:  # We're at root package level. Do not check for datasource.
            ensure_package_structure(path.parent)

        add_package_to_path(path.name, path)
        print(f"Target folder '{path.name}' was missing in '{path.parent}'. Created: ✓")


def get_root_packages_in_data_sources(path: str) -> dict:
    """
    Generate a dict that contains what root packages are included in a data source. Example structure:
    {
        "dataSourceA": [rootPackageA, rootPackageB],
        "dataSourceB": [rootPackageC]
    }
    """
    data_sources_dir, data_dir = get_app_dir_structure(Path(path))
    data_source_definitions: list[str] = get_json_files_in_dir(data_sources_dir)
    root_packages_in_data_sources = {}
    for data_source_definition in data_source_definitions:
        with open(os.path.join(data_sources_dir, data_source_definition)) as file:
            data_source_document = json.load(file)
            # Global folders should be uploaded directly to the data source
            # and should not be included in the root packages of the data source.
            global_folders = data_source_document.get("global_folders", [])
            data_source = data_source_document["name"]
            data_source_path = os.path.join(data_dir, data_source)
            root_packages: list[str] = [
                folder
                for folder in os.listdir(data_source_path)
                if os.path.isdir(os.path.join(data_source_path, folder)) and folder not in global_folders
            ]
            root_packages_in_data_sources[data_source] = root_packages
    return root_packages_in_data_sources


def validate_entities_in_data_sources(data_source_contents: dict):
    """Run validation on entities in data sources.
    data_source_contents is a dict that contains what root packages are included in a data source. Example structure:
    {
        "dataSourceA": [rootPackageA, rootPackageB],
        "dataSourceB": [rootPackageC]
    }

    """
    for data_source_name in data_source_contents:
        root_packages = data_source_contents[data_source_name]
        for root_package_name in root_packages:
            print("Validating entities in: ", f"{os.path.join(data_source_name, root_package_name)}")
            dmss_api.validate_existing_entity(f"{os.path.join(data_source_name, root_package_name)}")
