from __future__ import annotations

from datetime import datetime

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
        created_at: datetime

    with pytest.raises(AvroSchemaGenerationError, match="created_at"):
        Event.model_avro_schema()
