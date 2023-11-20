import json
from typing import Any, Callable

import requests
import typer
from rich.console import Console
from rich.text import Text
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from dm_cli.dmss_api import ApiException
from dm_cli.dmss_api.api.default_api import DefaultApi
from dm_cli.dmss_api.exceptions import NotFoundException
from dm_cli.state import state

console = Console()

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


@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    retry=retry_if_not_exception_type(ApplicationException),
)
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
    except ApplicationException as e:
        if state.debug:
            console.print_exception()
        exception = e.dict()
        console.print(exception, style="red1")
        raise typer.Exit(code=1)
    except (NotFoundException, ApiException) as e:
        if state.debug:
            console.print_exception()
        exception = json.loads(e.body)
        console.print(exception, style="red1")
        raise typer.Exit(code=1)
    except Exception as error:
        if state.debug:
            console.print_exception()
        text = Text(str(error))
        console.print(text, style="red1")
        raise typer.Exit(code=1)
