import io
import json
from json import JSONDecodeError
from pathlib import Path
from zipfile import ZipFile

from rich import print
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_not_exception_type,
    retry_if_not_result,
    stop_after_attempt,
    wait_random_exponential,
)

from .dmss import ApplicationException, dmss_api
from .dmss_api.exceptions import ApiException, NotFoundException, ServiceException
from .dmss_api.models.entity import Entity
from .domain import Package
from .import_package import import_package_content, import_package_tree
from .package_tree_from_zip import package_tree_from_zip
from .state import state
from .utils.reference import replace_relative_references
from .utils.utils import (
    concat_dependencies,
    console,
    dependencies_of,
    destination_is_root,
    ensure_package_structure,
)
from .utils.zip import zip_all


@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    retry=retry_if_exception_type(ServiceException),
)
def import_document(source_path: Path, destination: str, document: dict):
    old_dependencies = dependencies_of(dmss_api.export_meta(destination))

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


def import_single_entity(source_path: Path, destination: str, validate: bool = False):
    ensure_package_structure(Path(destination))
    print(f"Importing ENTITY '{source_path.name}' --> '{destination}'")

    try:  # Load the JSON document
        with open(source_path, "r") as fh:
            if Path(source_path).suffix == ".json":
                content = json.load(fh)
                if validate:
                    print(f"Validating {source_path}", end="")
                    dmss_api.validate_entity(Entity.from_dict(content))
                    print(" [green]✓[/green]")
                import_document(source_path, destination, content)
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
    retry=retry_if_exception_type(ServiceException),
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
        dependencies = dependencies_of(dmss_api.export_meta(destination))

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


def package_tree_from_folder(source_path: Path, destination: str, dependencies: dict):
    memory_file = io.BytesIO()
    with ZipFile(memory_file, mode="w") as zip_file:
        zip_all(
            zip_file,
            source_path,
            write_folder=True,
        )
    memory_file.seek(0)
    return package_tree_from_zip(
        destination,
        memory_file,
        is_root=False,
        extra_dependencies=dependencies,
        source_path=source_path,
    )


@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    retry=retry_if_exception_type(ServiceException),
)
def import_folders_as_one_package(source_path: Path, destination: str, package_name: str, validate: bool) -> None:
    """Import every folder in 'source_path' as the single package '<destination>/<package_name>'.

    Importing them one by one asks the server to link each folder into a package that is still being
    built, which costs six requests per folder and grows more expensive with every folder linked. The
    end state is one package holding all of them, and a package can be described in a single request,
    so describe it once: build the whole tree locally, link it into its parent with one write, and
    let its contents follow as raw documents.

    Each folder is turned into exactly the tree it would have become on its own, so references
    resolve as if it had been imported by itself. What changes is that the package they end up in is
    now written rather than accumulated, so it holds these folders and nothing else.
    """
    target = f"{destination}/{package_name}"
    if dmss_api.document_check(target):
        if not state.force:
            raise ValueError(f"Failed to upload to '{target}' - It already exists.")
        console.print(f"'{target}' already exists.  Replacing it...", style="dark_orange")
        dmss_api.document_remove(target)

    ensure_package_structure(Path(destination))
    dependencies = dependencies_of(dmss_api.export_meta(destination))

    entries = sorted(source_path.iterdir())
    package = Package(name=package_name)
    package.content = [package_tree_from_folder(folder, target, dependencies) for folder in entries if folder.is_dir()]

    print(f"Importing all content from '{source_path}/*' --> '{target}'")
    dmss_api.document_add(destination, json.dumps(package.to_dict()), files=[])
    import_package_content(package, destination.split("/")[0], target, resolve_local_ids=False)

    # Loose files are not part of the tree the folders form, so they are added to it afterwards.
    for file in entries:
        if file.is_file():
            import_single_entity(file, target, validate)

    if validate:
        print(f"Validating entities in: {target}")
        dmss_api.validate_existing_entity(target)
