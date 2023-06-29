import io
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Literal, NewType, Union
from uuid import UUID, uuid4

from .enums import SIMOS, ReferenceTypes


@dataclass(frozen=True)
class File:
    """Class for a file"""

    content: io.BytesIO
    path: Path
    name: str = ""
    uid: str = ""

    def __getitem__(self, item):
        return self.__getattribute__(item)


class Package:
    def __init__(
        self,
        name: str,
        description: str = "",
        uid: UUID = None,
        is_root: bool = False,
        meta: dict = None,
        parent: "Package" = None,
    ):
        self.name = name
        self.description = description
        self.uid = uid if uid else uuid4()
        self.is_root = is_root
        self.content: List[Union[Package, dict, File]] = []
        self.meta: Union[dict, None] = meta if meta else {}
        self.parent = parent if parent else None

    def __str__(self):
        return f"Name: {self.name}, Content: {len(self.content)}"

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def search(self, filename: str) -> Union["Package", dict]:
        return next((child for child in self.content if child["name"] == filename), None)

    def to_dict(self):
        return {
            "_id": str(self.uid),
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "isRoot": self.is_root,
            "_meta_": self.meta,
            "content": self._content_to_ref_dict(),
        }

    def path(self):
        if not self.parent:
            return self.name
        return f"{self.parent.path()}/{self.name}"

    def traverse_documents(self, func: Callable, update: bool = False, **kwargs) -> None:
        """
        Traverses the Package structure, calling the passed function on every non-Package node.

        @param func: A function that takes the document node as it's first parameter
        @param update: Whether to set the tree node to be the return value from the passed function
        @param kwargs: Keyword arguments to be passed to 'func'
        """
        for i, child in enumerate(self.content):
            if isinstance(child, Package):
                child.traverse_documents(func, update=update, **kwargs)
            else:
                child_file_path = self.path()  # The file's path in the package is needed to resolve dotted references
                if update:
                    self.content[i] = func(child, file_path=child_file_path, **kwargs)
                else:
                    func(child, file_path=child_file_path, **kwargs)

    def traverse_package(self, func: Callable, update: bool = False, **kwargs) -> None:
        """
        Traverses the Package structure, calling the passed function on every Package node.

        @param func: A function that takes the Package node as it's first parameter
        @param update: Whether to set the tree node to be the return value from the passed function
        @param kwargs: Keyword arguments to be passed to 'func'
        """
        for i, child in enumerate(self.content):
            if isinstance(child, Package):
                if update:
                    self.content[i] = func(child, **kwargs)
                else:
                    func(child, **kwargs)
                child.traverse_package(func, update, **kwargs)

    @property
    def type(self):
        return SIMOS.PACKAGE.value

    def _content_to_ref_dict(self):
        result = []
        for child in self.content:
            if isinstance(child, File):
                result.append(
                    {
                        "address": f"${str(child.uid)}",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": ReferenceTypes.STORAGE.value,
                    }
                )
            elif isinstance(child, Package):
                result.append(
                    {
                        "address": f"${str(child.uid)}",
                        "type": SIMOS.REFERENCE.value,
                        "referenceType": ReferenceTypes.STORAGE.value,
                    }
                )
            else:  # Assume the child is a dict
                if "name" in child:
                    result.append(
                        {
                            "address": f"${child['_id']}",
                            "type": SIMOS.REFERENCE.value,
                            "referenceType": ReferenceTypes.STORAGE.value,
                        }
                    )

                else:
                    result.append(
                        {
                            "address": f"${child['_id']}",
                            "type": SIMOS.REFERENCE.value,
                            "referenceType": ReferenceTypes.STORAGE.value,
                        }
                    )
        return result


TDependencyProtocol = NewType("TDependencyProtocol", Literal["dmss", "http"])


@dataclass(frozen=True)
class Dependency:
    """Class for any dependencies (external types) a entity references"""

    alias: str
    # Different ways we support to fetch dependencies.
    # dmss: Internally within the DMSS instance
    # http: A public HTTP GET call
    protocol: TDependencyProtocol
    address: str
    version: str = ""
    type: str = ""

    def __eq__(self, other):
        return (
            self.alias == other.alias
            and self.protocol == other.protocol
            and self.address == other.address
            and self.version == other.version
        )
