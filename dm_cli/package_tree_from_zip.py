import io
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Dict
from zipfile import ZipFile

from .domain import Package
from .import_package import (
    add_file_to_package,
    add_package_to_package,
    replace_relative_references,
)
from .utils import Dependency, concat_dependencies


def package_tree_from_zip(data_source_id: str, zip_package: io.BytesIO) -> Package:
    """
    Converts a Zip-folder into a DMSS Package structure.

    Inserting UUID4's between any references, converting relative paths to absolute paths,
    and dependencyAliases to absolute addresses.

    @param data_source_id: A string with the name/id of an existing data source to import package to
    @param zip_package: A zip-folder represented as an in-memory io.BytesIO object
    @return: A Package object with sub folders(Package) and documents(dict)
    """
    reference_table = {}

    with ZipFile(zip_package) as zip_file:
        folder_name = zip_file.filelist[0].filename.split("/", 1)[0]

        # Find the root packages package.json file
        package_file = next(
            (z for z in zip_file.filelist if z.filename == f"{folder_name}/package.json"),
            None,
        )

        package_entity = json.loads(zip_file.read(package_file.filename)) if package_file else {}
        if package_file in zip_file.filelist:
            zip_file.filelist.remove(package_file)
        dependencies: Dict[str, Dependency] = {}
        package_dependencies = {
            v["alias"]: Dependency(**v) for v in package_entity.get("_meta_", {}).get("dependencies", [])
        }
        dependencies.update(package_dependencies)
        root_package = Package(
            name=package_entity.get("name", folder_name),
            is_root=True,
            meta=package_entity.get("_meta_"),
        )
        # Construct a nested Package object of the package to import
        for file_info in zip_file.filelist:
            filename = file_info.filename.split("/", 1)[1]  # Remove RootPackage prefix
            if file_info.is_dir():
                if filename == "":  # Skip rootPackage
                    continue
                add_package_to_package(Path(filename), root_package)
                continue
            if Path(filename).suffix != ".json":
                continue
            try:
                json_doc = json.loads(zip_file.read(f"{folder_name}/{filename}"))
            except JSONDecodeError:
                raise Exception(f"Failed to load the file '{filename}' as a JSON document")

            add_file_to_package(Path(filename), root_package, json_doc)

            # Add dependencies from entity to the global dependencies list
            dependencies = concat_dependencies(
                json_doc.get("_meta_", {}).get("dependencies", []), dependencies, filename
            )

        # Now that we have the entire package as a Package tree, traverse it, and replace relative references
        root_package.traverse_documents(
            lambda document, file_path: {
                key: replace_relative_references(
                    key, value, dependencies, zip_file=zip_file, data_source=data_source_id, file_path=file_path
                )
                for key, value in document.items()
            },
            update=True,
        )

    return root_package
