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


class AccessLevel(
    schemas.EnumBase,
    schemas.StrSchema
):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.

    An enumeration.
    """


    class MetaOapg:
        enum_value_to_name = {
            "WRITE": "WRITE",
            "READ": "READ",
            "NONE": "NONE",
        }

    @schemas.classproperty
    def WRITE(cls):
        return cls("WRITE")

    @schemas.classproperty
    def READ(cls):
        return cls("READ")

    @schemas.classproperty
    def NONE(cls):
        return cls("NONE")
