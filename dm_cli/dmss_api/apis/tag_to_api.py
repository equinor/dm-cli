import typing_extensions

from dm_cli.dmss_api.apis.tags import TagValues
from dm_cli.dmss_api.apis.tags.default_api import DefaultApi
from dm_cli.dmss_api.apis.tags.access_control_api import AccessControlApi
from dm_cli.dmss_api.apis.tags.blob_api import BlobApi
from dm_cli.dmss_api.apis.tags.blueprint_api import BlueprintApi
from dm_cli.dmss_api.apis.tags.datasource_api import DatasourceApi
from dm_cli.dmss_api.apis.tags.lookup_table_api import LookupTableApi
from dm_cli.dmss_api.apis.tags.document_api import DocumentApi
from dm_cli.dmss_api.apis.tags.export_api import ExportApi
from dm_cli.dmss_api.apis.tags.health_check_api import HealthCheckApi
from dm_cli.dmss_api.apis.tags.entity_api import EntityApi
from dm_cli.dmss_api.apis.tags.reference_api import ReferenceApi
from dm_cli.dmss_api.apis.tags.search_api import SearchApi
from dm_cli.dmss_api.apis.tags.personal_access_token_api import PersonalAccessTokenApi
from dm_cli.dmss_api.apis.tags.whoami_api import WhoamiApi

TagToApi = typing_extensions.TypedDict(
    'TagToApi',
    {
        TagValues.DEFAULT: DefaultApi,
        TagValues.ACCESS_CONTROL: AccessControlApi,
        TagValues.BLOB: BlobApi,
        TagValues.BLUEPRINT: BlueprintApi,
        TagValues.DATASOURCE: DatasourceApi,
        TagValues.LOOKUPTABLE: LookupTableApi,
        TagValues.DOCUMENT: DocumentApi,
        TagValues.EXPORT: ExportApi,
        TagValues.HEALTH_CHECK: HealthCheckApi,
        TagValues.ENTITY: EntityApi,
        TagValues.REFERENCE: ReferenceApi,
        TagValues.SEARCH: SearchApi,
        TagValues.PERSONAL_ACCESS_TOKEN: PersonalAccessTokenApi,
        TagValues.WHOAMI: WhoamiApi,
    }
)

tag_to_api = TagToApi(
    {
        TagValues.DEFAULT: DefaultApi,
        TagValues.ACCESS_CONTROL: AccessControlApi,
        TagValues.BLOB: BlobApi,
        TagValues.BLUEPRINT: BlueprintApi,
        TagValues.DATASOURCE: DatasourceApi,
        TagValues.LOOKUPTABLE: LookupTableApi,
        TagValues.DOCUMENT: DocumentApi,
        TagValues.EXPORT: ExportApi,
        TagValues.HEALTH_CHECK: HealthCheckApi,
        TagValues.ENTITY: EntityApi,
        TagValues.REFERENCE: ReferenceApi,
        TagValues.SEARCH: SearchApi,
        TagValues.PERSONAL_ACCESS_TOKEN: PersonalAccessTokenApi,
        TagValues.WHOAMI: WhoamiApi,
    }
)
