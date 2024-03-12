from os.path import normpath
from pathlib import Path
from typing import Dict, List, Union

from ..dmss import ApplicationException
from ..domain import Dependency
from ..enums import SIMOS, BuiltinDataTypes, ReferenceTypes
from .utils import resolve_dependency


def resolve_reference(
    reference: str, dependencies: Dict[str, Dependency], destination: str, file_path: str | None
) -> str:
    destination = destination.rstrip("/")
    root_package = file_path.split("/", 1)[0] if file_path else ""
    try:
        if "://" in reference or reference == "_default_" or reference[0] == "^" or reference[0] == "~":
            return reference
        if ":" in reference:
            return resolve_dependency(reference, dependencies)
        if reference[0] == ".":
            normalized_dotted_ref: str = normpath(f"{file_path}/{reference}")
            return f"dmss://{destination}/{normalized_dotted_ref}"
        if reference[0] == "/":
            data_source = destination.split("/")[0]
            return f"dmss://{data_source}{reference}"
        return f"dmss://{destination}/{root_package}/{reference}"
    except ApplicationException as ex:
        ex.debug = f"File: {file_path}, Destination: {destination}, Root: {root_package}"
        raise ex


def replace_relative_references(
    value: dict | list,
    dependencies: Dict[str, Dependency],
    destination: str,
    file_path: Union[str, None] = None,
    source_path: Path = None,
) -> Union[str, List[str], dict]:
    """
    Takes a dict or list, and returns the passed value, with
    relative references replaced with absolute ones.

    For Blob-entities; insert the binary data from the file into the entity.
    It digs down on complex types

    @param value: Dict or list of an entity
    @param dependencies: A dict containing the dependencies of the document
    @param destination: The name of the data source where the document should be stored
    @param file_path: The path to the directory containing the documents

    When importing packages, the following additional parameter is required:
    @param zip_file:
    @param source_path: path to the root folder
    """

    def _resolve_reference(inner_value: str | None):
        if not inner_value:
            return inner_value
        return resolve_reference(
            inner_value,
            dependencies,
            destination,
            file_path,
        )

    def _replace_relative(inner_value: dict | list):
        return replace_relative_references(inner_value, dependencies, destination, file_path, source_path)

    if isinstance(value, dict):
        if not value:
            return value

        if not value.get("type"):
            raise KeyError(f"Object is missing the required 'type' attribute. File: '{file_path}'")

        value["type"] = _resolve_reference(value["type"])

        match _resolve_reference(value["type"]):
            case SIMOS.REFERENCE.value:
                if value["referenceType"] == ReferenceTypes.LINK.value:
                    value["address"] = _resolve_reference(value["address"])
                else:
                    # Handle storage references
                    local_file_path = "/".join(str(source_path).split("/")[:-1])
                    if value["address"][0] == ".":
                        raise ApplicationException(
                            f"Relative references by . are not supported", data=value, debug=file_path
                        )
                    value["address"] = f"{local_file_path}{value['address']}"
                return value

            case SIMOS.ATTRIBUTE.value:
                if enum_type := value.get("enumType"):
                    value["enumType"] = _resolve_reference(enum_type)
                if value["attributeType"] not in [data_type.value for data_type in BuiltinDataTypes]:
                    value["attributeType"] = _resolve_reference(value["attributeType"])
                    if default := value.get("default"):
                        value["default"] = _replace_relative(default)
                return value

            case SIMOS.BLUEPRINT.value:
                value["extends"] = [_resolve_reference(ext_from) for ext_from in value.get("extends", [])]
                value["attributes"] = [_replace_relative(attr) for attr in value.get("attributes", [])]
                if meta := value.get("_meta_"):
                    value["_meta_"] = _replace_relative(meta)
                return value

            case SIMOS.RECIPE_LINK.value:
                value["_blueprintPath_"] = _resolve_reference(value["_blueprintPath_"])
                if initial_recipe := value.get("initialUiRecipe"):
                    value["initialUiRecipe"] = _replace_relative(initial_recipe)
                if uiRecipes := value.get("uiRecipes"):
                    value["uiRecipes"] = _replace_relative(uiRecipes)
                return value

            case _:  # The value is a dict, but of unknown type. Need to dig through it recursively
                for key, inner_value in value.items():
                    if isinstance(inner_value, dict) or isinstance(inner_value, list):
                        value[key] = _replace_relative(inner_value)
                return value

    if isinstance(value, list):
        if value and (isinstance(value[0], dict) or isinstance(value[0], list)):
            return [_replace_relative(v) for v in value]
        # It's an empty or primitive list. Dig no further
        return value

    raise ValueError(f"Function can only be called on dicts and lists. Got {value}")
