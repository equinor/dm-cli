import io
import zipfile

import requests

from .dmss_api.api.default_api import DefaultApi

dmss_api = DefaultApi()


class Settings:
    PUBLIC_DMSS_API: str = "http://localhost:5000"
    DMSS_TOKEN: str | None = None


settings = Settings()


def export(absolute_document_ref: str):
    """Call export endpoint from DMSS to download document(s) as zip.

    The reason dmss_api cannot be used directly is that there were some issues with interpreting the JSON schema,
    which caused the export function in the generated DMSS api to not work properly.
    """
    headers = {"Access-Key": settings.DMSS_TOKEN}

    response = requests.get(f"{settings.PUBLIC_DMSS_API}/api/v1/export/{absolute_document_ref}", headers=headers)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    zip_file.extractall()
