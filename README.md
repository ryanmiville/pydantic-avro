# pydantic-avro

Thin Pydantic v2 integration for schemaless binary Avro records.

`pydantic-avro` gives Pydantic models an `AvroBaseModel` base class that can:

- generate a raw Avro record schema
- encode one schemaless Avro record as `bytes`
- decode that record back through normal Pydantic validation

It uses `fastavro` for the codec.

## Install

Requires Python 3.14 or newer.

Not published to PyPI yet. Install from GitHub for now:

```bash
uv add git+https://github.com/ryanmiville/pydantic-avro
# or
pip install git+https://github.com/ryanmiville/pydantic-avro
```

## Quickstart

```python
from typing import Literal

from pydantic import Field
from pydantic_avro import AvroBaseModel, AvroConfigDict


type Role = Literal["ADMIN", "USER"]


class User(AvroBaseModel):
    """A user account."""

    model_config = AvroConfigDict(avro_namespace="com.example")

    id: int = Field(serialization_alias="userId")
    name: str
    role: Role
    email: str | None = Field(default=None, description="Contact email")


user = User(id=1, name="Ada", role="ADMIN")

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
- named string Literal aliases (`type Role = Literal[...]`) as reusable Avro enums
- nested `AvroBaseModel` records
- nullable `T | None`

## Supported defaults

- primitive defaults (`None`, `bool`, `int`, `float`, `str`)
- enum and string `Literal[...]` field defaults
- representable collection defaults, recursively:
  - `list[T] = []` or `[value, ...]`
  - `dict[str, T] = {}` or `{"key": value, ...}`
- builtin empty factories only:
  - `Field(default_factory=list)` emits Avro default `[]`
  - `Field(default_factory=dict)` emits Avro default `{}`

Arbitrary factories are not called during schema generation.

## Out of scope for now

- Avro object container files
- schema registry wire formats
- Avro JSON encoding
- schema evolution with separate writer/reader schemas
- arbitrary unions beyond `T | None`
- recursive models
- decimal/date/time logical types
- anonymous `Literal[...]` inside containers
- non-string / invalid Avro enum symbols
- generic type aliases
- nested record defaults, except empty collections of records

Unsupported schema features raise `AvroSchemaGenerationError`.

## License

MIT
