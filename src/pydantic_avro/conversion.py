from __future__ import annotations

import types
from enum import Enum
from typing import Any, Union, get_args, get_origin

from pydantic_core import PydanticUndefined

from .schema import (
    avro_field_name,
    enum_value_symbol,
    enum_values_are_symbols,
    is_avro_model,
    unwrap_annotated,
)

_NONE_TYPE = type(None)


def to_avro_record(model_cls: type[Any], record: dict[str, Any]) -> dict[str, Any]:
    return {
        avro_field_name(python_name, field_info): to_avro_value(
            field_info.annotation,
            record.get(avro_field_name(python_name, field_info), PydanticUndefined),
        )
        for python_name, field_info in model_cls.model_fields.items()
        if avro_field_name(python_name, field_info) in record
    }


def from_avro_record(model_cls: type[Any], record: dict[str, Any]) -> dict[str, Any]:
    return {
        validation_field_name(python_name, field_info): from_avro_value(
            field_info.annotation,
            record[avro_field_name(python_name, field_info)],
        )
        for python_name, field_info in model_cls.model_fields.items()
        if avro_field_name(python_name, field_info) in record
    }


def validation_field_name(python_name: str, field_info: Any) -> str:
    if isinstance(field_info.alias, str):
        return field_info.alias
    return python_name


def to_avro_value(annotation: Any, value: Any) -> Any:
    if value is None or value is PydanticUndefined:
        return value

    annotation = unwrap_annotated(annotation)
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return to_avro_value(non_null_union_arg(annotation), value)
    if origin is list:
        (item_type,) = get_args(annotation)
        return [to_avro_value(item_type, item) for item in value]
    if origin is dict:
        _, value_type = get_args(annotation)
        return {key: to_avro_value(value_type, item) for key, item in value.items()}
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        enum_value = coerce_enum(annotation, value)
        return enum_value_symbol(enum_value) if enum_values_are_symbols(annotation) else enum_value.name
    if isinstance(annotation, type) and is_avro_model(annotation):
        nested = value.model_dump(by_alias=True, mode="python") if hasattr(value, "model_dump") else value
        return to_avro_record(annotation, nested)
    return value


def from_avro_value(annotation: Any, value: Any) -> Any:
    if value is None:
        return None

    annotation = unwrap_annotated(annotation)
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        return from_avro_value(non_null_union_arg(annotation), value)
    if origin is list:
        (item_type,) = get_args(annotation)
        return [from_avro_value(item_type, item) for item in value]
    if origin is dict:
        _, value_type = get_args(annotation)
        return {key: from_avro_value(value_type, item) for key, item in value.items()}
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        if enum_values_are_symbols(annotation):
            return value
        return annotation[str(value)]
    if isinstance(annotation, type) and is_avro_model(annotation):
        return from_avro_record(annotation, value)
    return value


def non_null_union_arg(annotation: Any) -> Any:
    non_null = [arg for arg in get_args(annotation) if unwrap_annotated(arg) is not _NONE_TYPE]
    if len(non_null) != 1:
        return annotation
    return non_null[0]


def coerce_enum(enum_cls: type[Enum], value: Any) -> Enum:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str) and value in enum_cls.__members__:
        return enum_cls[value]
    return enum_cls(value)
