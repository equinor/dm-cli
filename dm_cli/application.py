import json
import os
import re
from pathlib import Path
from typing import Dict, List, Union

import click

DATA_SOURCE_DEF_FILE_EXT: str = "json"


def _parse_alias_file(file_path: str) -> Dict[str, str]:
    regex = r"^[=A-Za-z0-9_-]*$"
    pattern = re.compile(regex)
    result: dict = {}
    try:
        with open(file_path) as alias_file:
            for line in alias_file.read().splitlines():
                if line.lstrip()[0] == "#":  # Skip commented lines
                    continue
                if not re.search(pattern, line):
                    raise ValueError(f"The alias file '{file_path}' is invalid. Invalid line '{line}'")
                key, value = line.split("=", 1)
                result[key] = value

    except FileNotFoundError:
        print("WARNING: No data source alias file found...")
    return result


def _replace_aliases_in_settings(settings: dict) -> dict:
    def replace_alias_in_reference(reference: Union[str, None]) -> Union[str, None]:
        if not reference:
            return
        if reference[0] == "/":  # Don't replace relative references
            return reference
        reference_data_source = reference.split("/", 1)[0]
        return reference.replace(
            reference_data_source,
            aliases.get(reference_data_source, reference_data_source),
            1,
        )

    aliases = settings["dataSourceAliases"]

    new_models: List[str] = []
    for model in settings.get("models", []):
        new_models.append(replace_alias_in_reference(model))

    new_actions: List[dict] = []
    for action in settings.get("actions", []):
        action["input"] = replace_alias_in_reference(action.get("input"))
        action["output"] = replace_alias_in_reference(action.get("output"))
        new_actions.append(action)

    settings["models"] = new_models
    settings["actions"] = new_actions

    return settings


def _load_app_settings(home: str):
    """Load application settings from under the specified home directory."""
    # Every folder under home represents a separate application
    applications = next(os.walk(home))[1]

    application_settings: Dict[str, dict] = {}

    for app in applications:
        try:
            with open(f"{home}/{app}/settings.json") as json_file:
                app_settings: dict = json.load(json_file)
                app_settings["fileLocation"] = json_file.name
                app_settings["dataSourceAliases"] = _parse_alias_file(f"{home}/{app}/data/_aliases_")
                code_gen_folder = Path(f"{home}/{app}/code_generators")
                if code_gen_folder.is_dir():
                    app_settings["codeGenerators"] = os.listdir(str(code_gen_folder))
                application_settings[app_settings["name"]] = _replace_aliases_in_settings(app_settings)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"No settings file found for the app '{app}'."
                "Each application requires a 'settings.json' file located at "
                f"'{home}/{{name-of-app}}/'"
            )
        except KeyError as e:
            raise KeyError(f"The settings file for the '{app}' application is invalid: {e}")
        print(f"Successfully loaded app '{app}'")

    return application_settings


def get_app_dir_structure(path: Path) -> [Path, Path]:
    app_dir = Path(path)
    if not app_dir.is_dir():
        raise FileNotFoundError(f"The path '{path}' is not a directory.")

    # Check for presence of expected directories, 'data_sources' and 'data'
    data_sources_dir = path.joinpath("data_sources")
    data_dir = path.joinpath("data")
    if not data_sources_dir.is_dir() or not data_dir.is_dir():
        click.echo(
            f"The directory '{path.name}' does not have the expected structure. It should contain two directories;"
        )
        click.echo(
            """
            ├── data
            └── data_sources
        """
        )
        exit(1)

    return data_sources_dir, data_dir


def get_data_source_definition_files(path: Path) -> List[str]:
    """Get all JSON files found in <path>."""
    return [filename for filename in os.listdir(path) if filename.endswith(f".{DATA_SOURCE_DEF_FILE_EXT}")]


def get_subdirectories(path: Path) -> List[str]:
    """Get all subdirectories found in <path>."""
    if not isinstance(path, Path):
        path = Path(path)

    return [dirname for dirname in os.listdir(path) if path.joinpath(dirname).is_dir()]
