# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from dm_cli.dmss_api.api.access_control_api import AccessControlApi
    from dm_cli.dmss_api.api.attribute_api import AttributeApi
    from dm_cli.dmss_api.api.blob_api import BlobApi
    from dm_cli.dmss_api.api.blueprint_api import BlueprintApi
    from dm_cli.dmss_api.api.datasource_api import DatasourceApi
    from dm_cli.dmss_api.api.default_api import DefaultApi
    from dm_cli.dmss_api.api.document_api import DocumentApi
    from dm_cli.dmss_api.api.entity_api import EntityApi
    from dm_cli.dmss_api.api.export_api import ExportApi
    from dm_cli.dmss_api.api.file_api import FileApi
    from dm_cli.dmss_api.api.health_check_api import HealthCheckApi
    from dm_cli.dmss_api.api.lookup_table_api import LookupTableApi
    from dm_cli.dmss_api.api.meta_api import MetaApi
    from dm_cli.dmss_api.api.personal_access_token_api import PersonalAccessTokenApi
    from dm_cli.dmss_api.api.search_api import SearchApi
    from dm_cli.dmss_api.api.whoami_api import WhoamiApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from dm_cli.dmss_api.api.access_control_api import AccessControlApi
from dm_cli.dmss_api.api.attribute_api import AttributeApi
from dm_cli.dmss_api.api.blob_api import BlobApi
from dm_cli.dmss_api.api.blueprint_api import BlueprintApi
from dm_cli.dmss_api.api.datasource_api import DatasourceApi
from dm_cli.dmss_api.api.default_api import DefaultApi
from dm_cli.dmss_api.api.document_api import DocumentApi
from dm_cli.dmss_api.api.entity_api import EntityApi
from dm_cli.dmss_api.api.export_api import ExportApi
from dm_cli.dmss_api.api.file_api import FileApi
from dm_cli.dmss_api.api.health_check_api import HealthCheckApi
from dm_cli.dmss_api.api.lookup_table_api import LookupTableApi
from dm_cli.dmss_api.api.meta_api import MetaApi
from dm_cli.dmss_api.api.personal_access_token_api import PersonalAccessTokenApi
from dm_cli.dmss_api.api.search_api import SearchApi
from dm_cli.dmss_api.api.whoami_api import WhoamiApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
