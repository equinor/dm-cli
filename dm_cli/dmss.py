from typing import Union

import requests

from dm_cli.dmss_api.api.default_api import DefaultApi

dmss_api = DefaultApi()


class Settings:
    PUBLIC_DMSS_API: str = "http://localhost:5000"
    DMSS_TOKEN: Union[str, None] = None


settings = Settings()


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


def export(absolute_document_ref: str):
    """Call export endpoint from DMSS to download document(s) as zip.

    The reason dmss_api cannot be used directly is that there were some issues with interpreting the JSON schema,
    which caused the export function in the generated DMSS api to not work properly.
    """
    headers = {"Access-Key": settings.DMSS_TOKEN}

    response = requests.get(f"{settings.PUBLIC_DMSS_API}/api/export/{absolute_document_ref}", headers=headers)
    if response.status_code != 200:
        raise ApplicationException(
            message=f"Could not export document(s) from {absolute_document_ref} (status code {response.status_code})."
        )

    return response
