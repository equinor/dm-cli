import os
from zipfile import ZipFile


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
