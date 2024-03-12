import io
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Union
from zipfile import ZipFile

from .domain import Dependency, File, Package
from .import_package import (
    add_file_to_package,
    add_object_to_package,
    add_package_to_package,
)
from .utils.reference import replace_relative_references
from .utils.utils import concat_dependencies


def package_tree_from_zip(
    destination: str,
    zip_package: io.BytesIO,
    is_root: bool = True,
    extra_dependencies: Union[Dict[str, Dependency], None] = None,
    source_path: Path = None,
) -> Package:
    """
    Converts a Zip-folder into a DMSS Package structure.

    Inserting UUID4's between any references, converting relative paths to absolute paths,
    and dependencyAliases to absolute addresses.

    @param destination: A string with the documentId for the target. Only a data source is allowed
    @param zip_package: A zip-folder represented as an in-memory io.BytesIO object
    @param source_path: path to the root folder

    @return: A Package object with sub folders(Package) and documents(dict)
    """

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
        dependencies: Dict[str, Dependency] = {
            dependency["alias"]: Dependency(**dependency)
            for dependency in package_entity.get("_meta_", {}).get("dependencies", [])
        }
        if extra_dependencies:
            dependencies.update(extra_dependencies)
        root_package = Package(
            name=package_entity.get("name", folder_name),
            is_root=is_root,
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
                file_like = io.BytesIO(zip_file.read(f"{folder_name}/{filename}"))
                file_like.name = Path(filename).name  # stem
                file_like.destination = Path(f"/{destination}/{folder_name}/{filename}").parent
                add_object_to_package(Path(filename), root_package, file_like)
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

        def replace(document, file_path):
            if not isinstance(document, File):
                document = replace_relative_references(
                    document,
                    dependencies,
                    destination,
                    file_path=file_path,
                    source_path=source_path,
                )
            return document

        # Now that we have the entire package as a Package tree, traverse it, and replace relative references
        root_package.traverse_documents(
            lambda document, file_path: replace(document, file_path),
            update=True,
        )
        root_package.meta = replace_relative_references(
            root_package.meta,
            dependencies,
            destination,
            file_path=root_package.path(),
            source_path=source_path,
        )
        root_package.traverse_package(
            lambda package: replace_relative_references(
                package.meta,
                dependencies,
                destination,
                file_path=package.path(),
                source_path=source_path,
            )
        )

    return root_package
