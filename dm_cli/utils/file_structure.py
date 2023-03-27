import os
from pathlib import Path
from typing import List

import typer

DATA_SOURCE_DEF_FILE_EXT: str = "json"


def get_app_dir_structure(path: Path) -> [Path, Path]:
    app_dir = Path(path)
    if not app_dir.is_dir():
        raise FileNotFoundError(f"The path '{path}' is not a directory.")

    # Check for presence of expected directories, 'data_sources' and 'data'
    data_sources_dir = path.joinpath("data_sources")
    data_dir = path.joinpath("data")
    if not data_sources_dir.is_dir() or not data_dir.is_dir():
        print(f"The directory '{path.name}' does not have the expected structure. It should contain two directories;")
        print(
            """
            ├── data
            └── data_sources
        """
        )
        raise typer.Exit(code=1)

    return data_sources_dir, data_dir


def get_json_files_in_dir(path: Path) -> List[str]:
    """Get all JSON files found in <path>."""
    return [filename for filename in os.listdir(path) if filename.endswith(f".{DATA_SOURCE_DEF_FILE_EXT}")]
