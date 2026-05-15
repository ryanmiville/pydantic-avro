from __future__ import annotations

import io
from typing import Any, cast
from weakref import WeakKeyDictionary

from fastavro import parse_schema, schemaless_reader, schemaless_writer

from .errors import AvroDecodeError, AvroEncodeError, AvroSchemaGenerationError
from .schema import generate_avro_schema

_PARSED_SCHEMA_CACHE: WeakKeyDictionary[type[Any], dict[str, Any]] = WeakKeyDictionary()


def get_parsed_schema(model_cls: type[Any]) -> dict[str, Any]:
    cached = _PARSED_SCHEMA_CACHE.get(model_cls)
    if cached is not None:
        return cached

    raw_schema = generate_avro_schema(model_cls)
    try:
        parsed_schema = cast(dict[str, Any], parse_schema(raw_schema))
    except Exception as exc:  # pragma: no cover - generate validates first
        raise AvroSchemaGenerationError(
            f"Generated Avro schema for {model_cls.__name__} is invalid"
        ) from exc
    _PARSED_SCHEMA_CACHE[model_cls] = parsed_schema
    return parsed_schema


def encode_avro(parsed_schema: dict[str, Any], record: dict[str, Any]) -> bytes:
    try:
        buffer = io.BytesIO()
        schemaless_writer(buffer, parsed_schema, record)
        return buffer.getvalue()
    except Exception as exc:
        raise AvroEncodeError("Failed to encode Avro message") from exc


def decode_avro(
    parsed_schema: dict[str, Any], data: bytes | bytearray | memoryview
) -> dict[str, Any]:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise AvroDecodeError("Avro message data must be bytes-like")

    try:
        buffer = io.BytesIO(bytes(data))
        decoded = schemaless_reader(buffer, parsed_schema)
    except Exception as exc:
        raise AvroDecodeError("Failed to decode Avro message") from exc

    if not isinstance(decoded, dict):
        raise AvroDecodeError("Decoded Avro message was not a record")
    return decoded
