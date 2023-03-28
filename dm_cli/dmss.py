import json
import traceback
from typing import Any, Callable

import requests
import typer
from rich import print

from dm_cli.dmss_api import ApiException
from dm_cli.dmss_api.api.default_api import DefaultApi
from dm_cli.dmss_api.exceptions import NotFoundException
from dm_cli.state import state

dmss_api = DefaultApi()


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
    headers = {"Access-Key": state.token}

    response = requests.get(f"{state.dmss_url}/api/export/{absolute_document_ref}", headers=headers)  # nosec
    if response.status_code != 200:
        raise ApplicationException(
            message=f"Could not export document(s) from {absolute_document_ref} (status code {response.status_code})."
        )

    return response


def dmss_exception_wrapper(
    function: Callable,
    *args,
    **kwargs,
) -> Any:
    try:
        return function(*args, **kwargs)
    except (ApplicationException, NotFoundException, ApiException) as e:
        if state.debug:
            traceback.print_exc()
        exception = json.loads(e.body)
        print(exception)
        raise typer.Exit(code=1)
    except Exception as error:
        traceback.print_exc()
        print(error)
        raise typer.Exit(code=1)
