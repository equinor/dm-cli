# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from dm_cli.dmss_api.paths.api_token import Api

from dm_cli.dmss_api.paths import PathValues

path = PathValues.API_TOKEN