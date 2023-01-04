# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from dm_cli.dmss_api.apis.tag_to_api import tag_to_api

import enum


class TagValues(str, enum.Enum):
    DEFAULT = "default"
    ACCESS_CONTROL = "access_control"
    BLOB = "blob"
    BLUEPRINT = "blueprint"
    DATASOURCE = "datasource"
    LOOKUPTABLE = "lookup-table"
    DOCUMENT = "document"
    EXPORT = "export"
    HEALTH_CHECK = "health_check"
    ENTITY = "entity"
    REFERENCE = "reference"
    SEARCH = "search"
    PERSONAL_ACCESS_TOKEN = "personal_access_token"
    WHOAMI = "whoami"
