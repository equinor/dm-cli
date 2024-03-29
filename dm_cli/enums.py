from enum import Enum


class StorageDataTypes(Enum):
    DEFAULT = "default"
    LARGE = "large"
    VERY_LARGE = "veryLarge"
    VIDEO = "video"
    BLOB = "blob"


class BuiltinDataTypes(Enum):
    STR = "string"
    NUM = "number"
    INT = "integer"
    BOOL = "boolean"
    OBJECT = "object"  # Any complex type (i.e. any blueprint type)
    BINARY = "binary"
    ANY = "any"

    def to_py_type(self):
        if self is BuiltinDataTypes.BOOL:
            return bool
        elif self is BuiltinDataTypes.INT:
            return int
        elif self is BuiltinDataTypes.NUM:
            return float
        elif self is BuiltinDataTypes.STR:
            return str
        elif self is BuiltinDataTypes.OBJECT:
            return dict


class SIMOS(Enum):
    BLOB = "dmss://system/SIMOS/Blob"
    PACKAGE = "dmss://system/SIMOS/Package"
    REFERENCE = "dmss://system/SIMOS/Reference"
    FILE = "dmss://system/SIMOS/File"
    DEPENDENCY = "dmss://system/SIMOS/Dependency"
    ATTRIBUTE = "dmss://system/SIMOS/BlueprintAttribute"
    BLUEPRINT = "dmss://system/SIMOS/Blueprint"
    RECIPE_LINK = "dmss://system/SIMOS/RecipeLink"


class ReferenceTypes(Enum):
    LINK = "link"
    POINTER = "pointer"
    STORAGE = "storage"
