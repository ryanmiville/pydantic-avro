# pydantic-avro

Thin Pydantic v2 integration for schemaless binary Avro records.

`pydantic-avro` gives Pydantic models an `AvroBaseModel` base class that can:

- generate a raw Avro record schema
- encode one schemaless Avro record as `bytes`
- decode that record back through normal Pydantic validation

It uses `fastavro` for the codec.

## Install

Not published to PyPI yet. Install from GitHub for now:

```bash
uv add git+https://github.com/ryanmiville/pydantic-avro
# or
pip install git+https://github.com/ryanmiville/pydantic-avro
```

## Quickstart

```python
from pydantic import Field
from pydantic_avro import AvroBaseModel, AvroConfigDict


class User(AvroBaseModel):
    """A user account."""

    model_config = AvroConfigDict(avro_namespace="com.example")

    id: int = Field(serialization_alias="userId")
    name: str
    email: str | None = Field(default=None, description="Contact email")


user = User(id=1, name="Ada")

schema = User.model_avro_schema()
payload = user.model_dump_avro()
round_tripped = User.model_validate_avro(payload)

assert round_tripped == user
```

See `examples/user.py` for a runnable smoke test.

## Supported types

- `None`
- `bool`
- `int` as Avro `long`
- `float` as Avro `double`
- `str`
- `bytes`
- `list[T]`
- `dict[str, T]`
- `Enum`
- string `Literal[...]` as Avro enum fields
- nested `AvroBaseModel` records
- nullable `T | None`

## Out of scope for now

- Avro object container files
- schema registry wire formats
- Avro JSON encoding
- schema evolution with separate writer/reader schemas
- arbitrary unions beyond `T | None`
- recursive models
- decimal/date/time logical types
- `Literal[...]` inside containers or with non-string / invalid Avro enum symbols

Unsupported schema features raise `AvroSchemaGenerationError`.

## License

MIT
