# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from dmss_api.paths.api_healthcheck import Api

from dmss_api.paths import PathValues

path = PathValues.API_HEALTHCHECK