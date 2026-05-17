from __future__ import annotations

import pytest

from pydantic_avro import (
    AvroDecodeError,
    AvroEncodeError,
    AvroSchemaGenerationError,
    PydanticAvroError,
    AvroBaseModel,
)


def test_public_exceptions_share_base() -> None:
    assert issubclass(AvroSchemaGenerationError, PydanticAvroError)
    assert issubclass(AvroEncodeError, PydanticAvroError)
    assert issubclass(AvroDecodeError, PydanticAvroError)


def test_unsupported_type_error_names_field() -> None:
    class Event(AvroBaseModel):
        coordinates: complex

    with pytest.raises(AvroSchemaGenerationError, match="coordinates"):
        Event.model_avro_schema()
