import os
from pathlib import Path
from zipfile import ZipFile

import emoji

from ..dmss import ApplicationException


def zip_all(zip_file: ZipFile, path: str, real_name="", write_folder: bool = True):
    basename = os.path.basename(path)
    if os.path.isdir(path):
        if real_name == "":
            real_name = basename
        if write_folder:
            zip_file.write(path, os.path.join(real_name))
        for root, dirs, files in os.walk(path):
            for d in dirs:
                zip_all(
                    zip_file,
                    os.path.join(root, d),
                    os.path.join(real_name, d),
                    write_folder=write_folder,
                )
            for f in files:
                zip_file.write(os.path.join(root, f), os.path.join(real_name, f))
            break
    elif os.path.isfile(path):
        zip_file.write(path, os.path.join(real_name, basename))
    else:
        pass


def unpack_and_save_zipfile(export_location: str, zip_file: ZipFile):
    """Unpack zipfile and save it to export_location. It is assumed that zip file only contains json files and folders.
    If file or folder to export already exists, an exception is raised.
    """
    zip_file_unpacked_path = f"{export_location}/{zip_file.filename.rstrip('.zip')}"

    zip_has_single_file_and_no_folders = (
        len(zip_file.filelist) == 1 and zip_file.filelist[0].filename.split("/")[0] == ""
    )
    if zip_has_single_file_and_no_folders:
        # If single file in the zip file (and the file is not inside a folder), the unpacked path has .json ending
        # (we assume the zip file always contains json files)
        zip_file_unpacked_path += ".json"

    if Path(zip_file_unpacked_path).exists():
        print(emoji.emojize(f"\t:error: File or folder '{zip_file_unpacked_path}' already exists. Exiting."))
        raise ApplicationException("Path already exists")

    zip_file.extractall(path=export_location)
    print(f"Saved unpacked zip file to '{zip_file_unpacked_path}'.")


def save_as_zip_file(export_location: str, filename: str, data: str):
    """Save binary data into a zip file on the local disk.
    If file or folder to export already exists, an exception is raised.
    """
    if not filename.endswith(".zip"):
        raise ApplicationException(message="file ending .zip must be included in filename!")
    saved_zip_file_path = f"{export_location}/{filename}"

    if Path(saved_zip_file_path).exists():
        print(emoji.emojize(f"\t:error: File or folder '{saved_zip_file_path}' already exists. Exiting."))
        raise ApplicationException("Path already exists")

    with open(saved_zip_file_path, "wb") as file:
        file.write(data)
        print(f"Wrote zip file to '{saved_zip_file_path}'")
