from __future__ import annotations

import json
from typing import Any

from typing_extensions import Self

from pydantic import BaseModel

from .codec import decode_avro, encode_avro, get_parsed_schema
from .conversion import from_avro_record, to_avro_record
from .schema import generate_avro_schema


class AvroBaseModel(BaseModel):
    """Base class for Avro schema generation and schemaless messages."""

    @classmethod
    def model_avro_schema(cls) -> dict[str, Any]:
        return generate_avro_schema(cls)

    @classmethod
    def model_avro_schema_json(cls) -> str:
        return json.dumps(cls.model_avro_schema(), separators=(",", ":"))

    def model_dump_avro(self) -> bytes:
        parsed_schema = get_parsed_schema(type(self))
        record = self.model_dump(by_alias=True, mode="python")
        return encode_avro(parsed_schema, to_avro_record(type(self), record))

    @classmethod
    def model_validate_avro(cls, data: bytes | bytearray | memoryview) -> Self:
        parsed_schema = get_parsed_schema(cls)
        decoded = decode_avro(parsed_schema, data)
        return cls.model_validate(
            from_avro_record(cls, decoded), by_alias=True, by_name=True
        )
