import io
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any, List, Tuple
from uuid import UUID, uuid4
from zipfile import ZipFile

from progress.bar import IncrementalBar

from .dmss import dmss_api
from .domain import Package
from .enums import SIMOS


class ApplicationException(Exception):
    status: int = 500
    type: str = "ApplicationException"
    message: str = "The requested operation failed"
    debug: str = "An unknown and unhandled exception occurred in the API"
    data: dict = None

    def __init__(
        self,
        message: str = "The requested operation failed",
        debug: str = "An unknown and unhandled exception occurred in the API",
        data: dict = None,
        status: int = 500,
    ):
        self.status = status
        self.type = self.__class__.__name__
        self.message = message
        self.debug = debug
        self.data = data

    def dict(self):
        return {
            "status": self.status,
            "type": self.type,
            "message": self.message,
            "debug": self.debug,
            "data": self.data,
        }


from dataclasses import dataclass
from typing import Literal, NewType

TDependencyProtocol = NewType("TDependencyProtocol", Literal["sys", "http"])


@dataclass(frozen=True)
class Dependency:
    """Class for any dependencies (external types) a entity references"""

    alias: str
    # Different ways we support to fetch dependencies.
    # sys: Internally within the DMSS instance
    # http: A public HTTP GET call
    protocol: TDependencyProtocol
    address: str
    version: str = ""


keys_to_check = (
    "type",
    "attributeType",
    "_id",
    "extends",
)  # These keys may contain a reference


def resolve_dependency(type_ref: str, dependencies: List[Dependency]) -> str:
    """Takes a type reference and a list of dependencies. Returns the address for
    the Blueprint, prefixed with which protocol should be used to fetch it.
    Expected format is ALIAS:ADDRESS"""
    tag, path = type_ref.split(":", 1)
    path = path.strip(" /")
    dependency = next((d for d in dependencies if d.alias == tag), None)
    if not dependency:
        raise ApplicationException(
            f"No dependency with alias '{tag}' was found in the entities dependencies list"
        )

    if dependency.protocol == "sys":
        address = dependency.address.strip(" /")
        return f"sys://{address}/{path}"
    if dependency.protocol == "http":
        raise NotImplementedError

    raise ApplicationException(
        f"Protocol '{dependency.protocol}' is not a valid protocol for resolving dependencies"
    )


def replace_relative_references(
    key: str,
    value,
    reference_table: dict = None,
    zip_file: ZipFile = None,
    dependencies: List[Dependency] | None = None,
) -> Any:
    """
    Takes a key-value pair and returns the passed value, with relative references updated with absolute ones found in the 'reference_table'.

    For Blob-entities. Insert the binary data from the file into the entity.
    It digs down on complex types.

    @param reference_table: A dict like so; {"fileName": {"id": newUUID, "absolute": ds/root-package/file}
    @param key: Name of the attribute being checked in the document
    @param value: Value of the attribute being checked in the document
    @return: The passed value, with relative references updated with absolute ones
    """
    if key in keys_to_check:
        if key == "_id":
            try:
                UUID(value)  # If _id is a valid uuid, don't change it
                return value
            except ValueError:  # The _id is not a UUID. It should then be an alias
                try:
                    return next(
                        (
                            doc["id"]
                            for doc in reference_table.values()
                            if doc["alias"] == value
                        )
                    )
                except StopIteration:
                    raise ApplicationException(
                        f"IMPORT ERROR: No document with the alias '{value}' was found in the reference table."
                    )
        if key == "extends":  # 'extends' is a list
            extends_list = []
            for i, blueprint in enumerate(value):
                if ":" in blueprint:
                    extends_list.append(resolve_dependency(blueprint, dependencies))
                    continue
                # Relative references start with a "/", if not, they are absolute references
                if blueprint[0] == "/":
                    try:
                        extends_list.append(reference_table[value[i]]["absolute"])
                    except KeyError:
                        raise ApplicationException(
                            "Import failed",
                            debug=f"Failed to find the relative reference '{value[i]}' in the reference table.",
                            data=value,
                        )
                    continue
                extends_list.append(blueprint)
            return extends_list
        if ":" in value:
            return resolve_dependency(value, dependencies)
        if value[0] == "/":
            try:
                return reference_table[value]["absolute"]
            except KeyError:
                raise ApplicationException(
                    f"IMPORT ERROR: Failed to find the relative reference '{value}' in the reference table."
                )

    # If the value is a complex type, dig down recursively
    if isinstance(value, dict) and value != {}:
        # First check if the type is a blob type
        if (
            replace_relative_references(
                "type", value["type"], reference_table, zip_file, dependencies
            )
            == SIMOS.BLOB.value
        ):
            # Add blob data to the blob-entity
            if (
                value["name"][0] == "/"
            ):  # It's a relative reference to the blob file. Get root_package_name...
                root_package_name = f"{zip_file.filelist[0].filename.split('/', 1)[0]}"
                # '_blob_data' is a temporary key for keeping the binary data
                return {
                    "_blob_data_": zip_file.read(f"{root_package_name}{value['name']}"),
                    **value,
                    "type": SIMOS.BLOB.value,
                }

            return {"_blob_data_": zip_file.read(value["name"]), **value}

        return {
            k: replace_relative_references(
                k, v, reference_table, zip_file, dependencies
            )
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [
            replace_relative_references(key, v, reference_table, zip_file, dependencies)
            for v in value
        ]

    return (
        value  # This means it's a primitive type with an absolute path, return it as is
    )


def add_file_to_package(
    path: Path, package: Package, document: dict
) -> Tuple[UUID, str]:
    if len(path.parts) == 1:  # End of path means the actual document
        uid = uuid4()
        # If the document has an "_id", return it as an alias, if not use UUID as alias.
        alias = document.get("_id", str(uid))
        package.content.append({**document, "_id": alias})
        return uid, alias

    sub_folder = next((p for p in package.content if p["name"] == path.parts[0]), None)
    if (
        not sub_folder
    ):  # If the sub folder has not already been created on parent, create it
        sub_folder = Package(name=path.parts[0])
        package.content.append(sub_folder)

    new_path = str(path).split("/", 1)[
        1
    ]  # Remove first element in path before stepping down
    return add_file_to_package(Path(new_path), sub_folder, document)


def add_package_to_package(path: Path, package: Package) -> None:
    if len(path.parts) == 1:
        package.content.append(Package(name=path.parts[0]))
        return

    sub_folder = next((p for p in package.content if p["name"] == path.parts[0]), None)
    if (
        not sub_folder
    ):  # If the sub folder has not already been created on parent, create it
        sub_folder = Package(name=path.parts[0])
        package.content.append(sub_folder)

    new_path = str(path).split("/", 1)[
        1
    ]  # Remove first element in path before stepping down
    return add_package_to_package(Path(new_path), sub_folder)


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
            (
                z
                for z in zip_file.filelist
                if z.filename == f"{folder_name}/package.json"
            ),
            None,
        )

        package_entity = (
            json.loads(zip_file.read(package_file.filename)) if package_file else {}
        )
        dependencies = [
            Dependency(**d)
            for d in package_entity.get("_meta_", {}).get("dependencies", [])
        ]
        root_package = Package(
            name=package_entity.get("name", folder_name), is_root=True
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
                raise Exception(
                    f"Failed to load the file '{filename}' as a JSON document"
                )
            uid, alias = add_file_to_package(Path(filename), root_package, json_doc)

            # Use the "name" attribute as the last element in the
            # reference path, so filename and "name" don't need to match
            if "name" in json_doc:
                if "/" in filename:
                    relative_path = (
                        f"/{'/'.join(filename.split('/')[:-1])}/{json_doc['name']}"
                    )
                else:
                    relative_path = f"/{json_doc['name']}"
            else:
                relative_path = f"/{filename}"
            # Create a dict with new UUID's and absolute references for every file in the package
            reference_table.update(
                {
                    relative_path: {
                        "filename": filename,
                        "alias": alias,
                        "id": str(uid),
                        "absolute": f"sys://{data_source_id}/{package_entity.get('name', folder_name)}{relative_path}",
                    }
                }
            )

        # Now that we have the entire package as a Package tree, traverse it, and replace relative references
        root_package.traverse_documents(
            lambda document: {
                k: replace_relative_references(
                    k,
                    v,
                    reference_table=reference_table,
                    zip_file=zip_file,
                    dependencies=dependencies,
                )
                for k, v in document.items()
                if k != "_meta_"  # Don't update references in "_meta_"
            },
            update=True,
        )

    return root_package


def upload_blobs_in_document(document: dict, data_source_id: str) -> dict:
    """Uploads any 'system/SIMOS/Blob' types in the document, and replacing the data with created uuid's."""
    try:
        if document["type"] == SIMOS.BLOB.value:
            blob_id = document.get("_blob_id", str(uuid4()))
            blob_name = Path(document["name"]).stem
            file_like = io.BytesIO(document["_blob_data_"])
            file_like.name = blob_name
            dmss_api.blob_upload(data_source_id, blob_id, file_like)
            return {
                "name": blob_name,
                "type": SIMOS.BLOB.value,
                "_blob_id": blob_id,
                "size": len(document["_blob_data_"]),
            }
    except KeyError as error:
        reduced_document = {k: v for k, v in document.items() if isinstance(v, str)}
        raise KeyError(
            f"The document; '{reduced_document}' is missing a required attribute: {error}"
        )
    for key, value in document.items():
        if isinstance(value, dict) and value:
            document[key] = upload_blobs_in_document(value, data_source_id)
        if isinstance(value, list) and value:
            if len(value) > 0 and isinstance(value[0], dict):
                document[key] = [
                    upload_blobs_in_document(item, data_source_id)
                    for item in document[key]
                ]
    return document


def import_package_tree(root_package: Package, data_source_id: str) -> None:
    documents_to_upload: List[dict] = [root_package.to_dict()]
    root_package.traverse_documents(
        lambda document: documents_to_upload.append(document)
    )
    root_package.traverse_package(
        lambda package: documents_to_upload.append(package.to_dict())
    )

    with IncrementalBar(
        f"\tImporting {root_package.name}",
        max=len(documents_to_upload),
        suffix="%(percent).0f%% - [%(eta)ds/%(elapsed)ds]",
    ) as bar:
        for document in documents_to_upload:
            document = upload_blobs_in_document(document, data_source_id)
            dmss_api.document_add_simple(data_source_id, document)
        bar.next()
