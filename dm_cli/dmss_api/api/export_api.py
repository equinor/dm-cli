"""
    Data Modelling Storage Service

    API for basic data modelling interaction  # noqa: E501

    The version of the OpenAPI document: 0.1.0
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


class ExportApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

        def __export(
            self,
            absolute_document_ref,
            **kwargs
        ):
            """Export  # noqa: E501

            Download a zip-folder with one or more documents as json file(s).  absolute_document_ref is on the format: 'DATASOURCE/PACKAGE/{ENTITY.name/ENTITY._id}  # noqa: E501
            This method makes a synchronous HTTP request by default. To make an
            asynchronous HTTP request, please pass async_req=True

            >>> thread = api.export(absolute_document_ref, async_req=True)
            >>> result = thread.get()

            Args:
                absolute_document_ref (str):

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
                _host_index (int/None): specifies the index of the server
                    that we want to use.
                    Default is read from the configuration.
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
            kwargs['_host_index'] = kwargs.get('_host_index')
            kwargs['absolute_document_ref'] = \
                absolute_document_ref
            return self.call_with_http_info(**kwargs)

        self.export = _Endpoint(
            settings={
                'response_type': None,
                'auth': [
                    'APIKeyHeader',
                    'OAuth2AuthorizationCodeBearer'
                ],
                'endpoint_path': '/api/export/{absolute_document_ref}',
                'operation_id': 'export',
                'http_method': 'GET',
                'servers': None,
            },
            params_map={
                'all': [
                    'absolute_document_ref',
                ],
                'required': [
                    'absolute_document_ref',
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
                    'absolute_document_ref':
                        (str,),
                },
                'attribute_map': {
                    'absolute_document_ref': 'absolute_document_ref',
                },
                'location_map': {
                    'absolute_document_ref': 'path',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/zip',
                    'application/json',
                    'text/plain'
                ],
                'content_type': [],
            },
            api_client=api_client,
            callable=__export
        )

        def __export_meta(
            self,
            absolute_document_ref,
            **kwargs
        ):
            """Export Meta  # noqa: E501

            Export only the metadata of an entity. Entities must be specified on the format 'DATASOURCE/PACKAGE/{ENTITY.name/ENTITY._id} An entities metadata is concatenated from the \"top down\". Inheriting parents meta, and overriding for any specified further down.  If no metadata is defined anywhere in the tree, an empty object is returned.  # noqa: E501
            This method makes a synchronous HTTP request by default. To make an
            asynchronous HTTP request, please pass async_req=True

            >>> thread = api.export_meta(absolute_document_ref, async_req=True)
            >>> result = thread.get()

            Args:
                absolute_document_ref (str):

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
                _host_index (int/None): specifies the index of the server
                    that we want to use.
                    Default is read from the configuration.
                async_req (bool): execute request asynchronously

            Returns:
                bool, date, datetime, dict, float, int, list, str, none_type
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
            kwargs['_host_index'] = kwargs.get('_host_index')
            kwargs['absolute_document_ref'] = \
                absolute_document_ref
            return self.call_with_http_info(**kwargs)

        self.export_meta = _Endpoint(
            settings={
                'response_type': (bool, date, datetime, dict, float, int, list, str, none_type,),
                'auth': [
                    'APIKeyHeader',
                    'OAuth2AuthorizationCodeBearer'
                ],
                'endpoint_path': '/api/export/meta/{absolute_document_ref}',
                'operation_id': 'export_meta',
                'http_method': 'GET',
                'servers': None,
            },
            params_map={
                'all': [
                    'absolute_document_ref',
                ],
                'required': [
                    'absolute_document_ref',
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
                    'absolute_document_ref':
                        (str,),
                },
                'attribute_map': {
                    'absolute_document_ref': 'absolute_document_ref',
                },
                'location_map': {
                    'absolute_document_ref': 'path',
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
            api_client=api_client,
            callable=__export_meta
        )
