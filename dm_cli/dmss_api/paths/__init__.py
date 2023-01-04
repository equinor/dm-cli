# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from dm_cli.dmss_api.apis.path_to_api import path_to_api

import enum


class PathValues(str, enum.Enum):
    API_ACL_DATA_SOURCE_ID_DOCUMENT_ID = "/api/acl/{data_source_id}/{document_id}"
    API_BLOBS_DATA_SOURCE_ID_BLOB_ID = "/api/blobs/{data_source_id}/{blob_id}"
    API_BLUEPRINT_TYPE_REF = "/api/blueprint/{type_ref}"
    API_RESOLVEPATH_ABSOLUTE_ID = "/api/resolve-path/{absolute_id}"
    API_DATASOURCES_DATA_SOURCE_ID = "/api/data-sources/{data_source_id}"
    API_DATASOURCES = "/api/data-sources"
    API_DOCUMENTS_ID_REFERENCE = "/api/documents/{id_reference}"
    API_DOCUMENTSBYPATH_ABSOLUTE_PATH = "/api/documents-by-path/{absolute_path}"
    API_DOCUMENTS_DATA_SOURCE_ID_DOCUMENT_ID = "/api/documents/{data_source_id}/{document_id}"
    API_DOCUMENTS_DATA_SOURCE_ID_DOTTED_ID = "/api/documents/{data_source_id}/{dotted_id}"
    API_DOCUMENTS_PATH_REFERENCE_ADDTOPATH = "/api/documents/{path_reference}/add-to-path"
    API_DOCUMENTS_DATA_SOURCE_ID_ADDRAW = "/api/documents/{data_source_id}/add-raw"
    API_DOCUMENTS_ABSOLUTE_REF = "/api/documents/{absolute_ref}"
    API_DOCUMENTS_DATA_SOURCE_ID_REMOVEBYPATH_DIRECTORY = "/api/documents/{data_source_id}/remove-by-path/{directory}"
    API_EXPORT_META_ABSOLUTE_DOCUMENT_REF = "/api/export/meta/{absolute_document_ref}"
    API_EXPORT_ABSOLUTE_DOCUMENT_REF = "/api/export/{absolute_document_ref}"
    API_REFERENCE_DATA_SOURCE_ID_DOCUMENT_DOTTED_ID = "/api/reference/{data_source_id}/{document_dotted_id}"
    API_SEARCH = "/api/search"
    API_WHOAMI = "/api/whoami"
    API_ENTITY = "/api/entity"
    API_APPLICATION_APPLICATION = "/api/application/{application}"
    API_TOKEN = "/api/token"
    API_TOKEN_TOKEN_ID = "/api/token/{token_id}"
    API_HEALTHCHECK = "/api/healthcheck"
