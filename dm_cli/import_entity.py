import json
from json import JSONDecodeError
from pathlib import Path

from .dmss import dmss_api
from .domain import Dependency
from .utils import (
    concat_dependencies,
    replace_relative_references,
    upload_blobs_in_document,
)


def import_single_entity(path: Path, path_reference: str):
    data_source_id, package = path_reference.split("/", 1)

    # Load the JSON document
    try:
        with open(path, "r") as fh:
            document = json.load(fh)
    except JSONDecodeError:
        raise Exception(f"Failed to load the file '{path.name}' as a JSON document")

    remote_dependencies = dmss_api.export_meta(f"{data_source_id}/{package}")
    old_dependencies = {v["alias"]: Dependency(**v) for v in remote_dependencies.get("dependencies", [])}

    dependencies = concat_dependencies(
        new_dependencies=document.get("_meta_", {}).get("dependencies", []),
        old_dependencies=old_dependencies,
        filename=path.name,
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
            parent_directory=path.parent,
        )

    # Upload blobs
    prepared_document = upload_blobs_in_document(prepared_document, data_source_id)
    document_json_str = json.dumps(prepared_document)

    dmss_api.document_add_to_path(
        f"{path_reference}",
        document_json_str,
        update_uncontained=True,
        files=[],
    )
