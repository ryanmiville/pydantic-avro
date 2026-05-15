class PydanticAvroError(Exception):
    """Base exception for pydantic-avro owned failures."""


class AvroSchemaGenerationError(PydanticAvroError):
    """Raised when a Pydantic model cannot produce a valid Avro schema."""


class AvroEncodeError(PydanticAvroError):
    """Raised when an Avro message cannot be encoded."""


class AvroDecodeError(PydanticAvroError):
    """Raised when an Avro message cannot be decoded."""
