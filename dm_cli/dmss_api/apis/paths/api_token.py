from dm_cli.dmss_api.paths.api_token.get import ApiForget
from dm_cli.dmss_api.paths.api_token.post import ApiForpost


class ApiToken(
    ApiForget,
    ApiForpost,
):
    pass
