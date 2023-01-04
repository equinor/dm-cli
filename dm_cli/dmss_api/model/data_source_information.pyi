# coding: utf-8

"""
    Data Modelling Storage Service

    API for basic data modelling interaction  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Generated by: https://openapi-generator.tech
"""

from datetime import date, datetime  # noqa: F401
import decimal  # noqa: F401
import functools  # noqa: F401
import io  # noqa: F401
import re  # noqa: F401
import typing  # noqa: F401
import typing_extensions  # noqa: F401
import uuid  # noqa: F401

import frozendict  # noqa: F401

from dmss_api import schemas  # noqa: F401


class DataSourceInformation(
    schemas.DictSchema
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """


    class MetaOapg:
        required = {
            "name",
            "id",
        }

        class properties:
            id = schemas.StrSchema
            name = schemas.StrSchema
            host = schemas.StrSchema
            type = schemas.StrSchema
            __annotations__ = {
                "id": id,
                "name": name,
                "host": host,
                "type": type,
            }

    name: MetaOapg.properties.name
    id: MetaOapg.properties.id

    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["id"]) -> MetaOapg.properties.id: ...

    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["name"]) -> MetaOapg.properties.name: ...

    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["host"]) -> MetaOapg.properties.host: ...

    @typing.overload
    def __getitem__(self, name: typing_extensions.Literal["type"]) -> MetaOapg.properties.type: ...

    @typing.overload
    def __getitem__(self, name: str) -> schemas.UnsetAnyTypeSchema: ...

    def __getitem__(self, name: typing.Union[typing_extensions.Literal["id", "name", "host", "type", ], str]):
        # dict_instance[name] accessor
        return super().__getitem__(name)


    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["id"]) -> MetaOapg.properties.id: ...

    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["name"]) -> MetaOapg.properties.name: ...

    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["host"]) -> typing.Union[MetaOapg.properties.host, schemas.Unset]: ...

    @typing.overload
    def get_item_oapg(self, name: typing_extensions.Literal["type"]) -> typing.Union[MetaOapg.properties.type, schemas.Unset]: ...

    @typing.overload
    def get_item_oapg(self, name: str) -> typing.Union[schemas.UnsetAnyTypeSchema, schemas.Unset]: ...

    def get_item_oapg(self, name: typing.Union[typing_extensions.Literal["id", "name", "host", "type", ], str]):
        return super().get_item_oapg(name)


    def __new__(
        cls,
        *args: typing.Union[dict, frozendict.frozendict, ],
        name: typing.Union[MetaOapg.properties.name, str, ],
        id: typing.Union[MetaOapg.properties.id, str, ],
        host: typing.Union[MetaOapg.properties.host, str, schemas.Unset] = schemas.unset,
        type: typing.Union[MetaOapg.properties.type, str, schemas.Unset] = schemas.unset,
        _configuration: typing.Optional[schemas.Configuration] = None,
        **kwargs: typing.Union[schemas.AnyTypeSchema, dict, frozendict.frozendict, str, date, datetime, uuid.UUID, int, float, decimal.Decimal, None, list, tuple, bytes],
    ) -> 'DataSourceInformation':
        return super().__new__(
            cls,
            *args,
            name=name,
            id=id,
            host=host,
            type=type,
            _configuration=_configuration,
            **kwargs,
        )
