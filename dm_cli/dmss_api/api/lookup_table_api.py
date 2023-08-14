"""
    Data Modelling Storage Service

    API for basic data modelling interaction  # noqa: E501

    The version of the OpenAPI document: 1.2.3
    Generated by: https://openapi-generator.tech
"""


import re  # noqa: F401
import sys  # noqa: F401

from dm_cli.dmss_api.api_client import ApiClient, Endpoint as _Endpoint
from dm_cli.dmss_api.model_utils import (  # noqa: F401
    check_allowed_values,
    check_validations,
    date,
    datetime,
    file_type,
    none_type,
    validate_and_convert_types
)
from dm_cli.dmss_api.model.error_response import ErrorResponse
from dm_cli.dmss_api.model.lookup import Lookup


class LookupTableApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client
        self.create_lookup_endpoint = _Endpoint(
            settings={
                'response_type': None,
                'auth': [
                    'APIKeyHeader',
                    'OAuth2AuthorizationCodeBearer'
                ],
                'endpoint_path': '/api/application/{application}',
                'operation_id': 'create_lookup',
                'http_method': 'POST',
                'servers': None,
            },
            params_map={
                'all': [
                    'application',
                    'recipe_package',
                ],
                'required': [
                    'application',
                    'recipe_package',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'application':
                        (str,),
                    'recipe_package':
                        ([str],),
                },
                'attribute_map': {
                    'application': 'application',
                    'recipe_package': 'recipe_package',
                },
                'location_map': {
                    'application': 'path',
                    'recipe_package': 'query',
                },
                'collection_format_map': {
                    'recipe_package': 'multi',
                }
            },
            headers_map={
                'accept': [
                    'application/json',
                    'text/plain'
                ],
                'content_type': [],
            },
            api_client=api_client
        )
        self.get_lookup_endpoint = _Endpoint(
            settings={
                'response_type': (Lookup,),
                'auth': [
                    'APIKeyHeader',
                    'OAuth2AuthorizationCodeBearer'
                ],
                'endpoint_path': '/api/application/{application}',
                'operation_id': 'get_lookup',
                'http_method': 'GET',
                'servers': None,
            },
            params_map={
                'all': [
                    'application',
                ],
                'required': [
                    'application',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'application':
                        (str,),
                },
                'attribute_map': {
                    'application': 'application',
                },
                'location_map': {
                    'application': 'path',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json',
                    'text/plain'
                ],
                'content_type': [],
            },
            api_client=api_client
        )

    def create_lookup(
        self,
        application,
        recipe_package,
        **kwargs
    ):
        """Create Lookup  # noqa: E501

        Create a recipe lookup table from a package containing RecipeLinks. Associate it with an application. This can be used for setting Ui- and StorageRecipes for specific applications.  - **application**: name of application - **recipe_package**: List with one or more paths to package(s) that contain recipe links. (Example: 'system/SIMOS/recipe_links')  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.create_lookup(application, recipe_package, async_req=True)
        >>> result = thread.get()

        Args:
            application (str):
            recipe_package ([str]):

        Keyword Args:
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            _request_auths (list): set to override the auth_settings for an a single
                request; this effectively ignores the authentication
                in the spec for a single request.
                Default is None
            async_req (bool): execute request asynchronously

        Returns:
            None
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['_request_auths'] = kwargs.get('_request_auths', None)
        kwargs['application'] = \
            application
        kwargs['recipe_package'] = \
            recipe_package
        return self.create_lookup_endpoint.call_with_http_info(**kwargs)

    def get_lookup(
        self,
        application,
        **kwargs
    ):
        """Get Lookup  # noqa: E501

        Fetch a single lookup table.  - **application**: name of application  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.get_lookup(application, async_req=True)
        >>> result = thread.get()

        Args:
            application (str):

        Keyword Args:
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _spec_property_naming (bool): True if the variable names in the input data
                are serialized names, as specified in the OpenAPI document.
                False if the variable names in the input data
                are pythonic names, e.g. snake case (default)
            _content_type (str/None): force body content-type.
                Default is None and content-type will be predicted by allowed
                content-types and body.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            _request_auths (list): set to override the auth_settings for an a single
                request; this effectively ignores the authentication
                in the spec for a single request.
                Default is None
            async_req (bool): execute request asynchronously

        Returns:
            Lookup
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_spec_property_naming'] = kwargs.get(
            '_spec_property_naming', False
        )
        kwargs['_content_type'] = kwargs.get(
            '_content_type')
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['_request_auths'] = kwargs.get('_request_auths', None)
        kwargs['application'] = \
            application
        return self.get_lookup_endpoint.call_with_http_info(**kwargs)

