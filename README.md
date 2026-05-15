# pydantic-avro

`pydantic-avro` maps Pydantic models to Avro's schema-driven binary record format.

The v0 goal is intentionally small: define an `AvroBaseModel` that can generate an Avro schema, encode one schemaless binary Avro record, and decode that record back into the Pydantic model.

## API

```python
from pydantic import Field
from pydantic_avro import AvroBaseModel, AvroConfigDict


class User(AvroBaseModel):
    """A user account."""

    model_config = AvroConfigDict(avro_namespace="com.example")

    id: int
    name: str
    email: str | None = Field(default=None, description="Contact email")


user = User(id=1, name="Ada")

schema: dict = User.model_avro_schema()
schema_json: str = User.model_avro_schema_json()

message: bytes = user.model_dump_avro()
round_tripped: User = User.model_validate_avro(message)
```

## Public exports for v0

```python
from pydantic_avro import (
    AvroBaseModel,
    AvroConfigDict,
    PydanticAvroError,
    AvroSchemaGenerationError,
    AvroEncodeError,
    AvroDecodeError,
)
```

No `AvroTypeAdapter` or standalone encode/decode functions in v0.

## Wire format

An **Avro Message** means one schemaless binary Avro record encoded with the model's generated Avro schema.

Out of scope for v0:

- Avro object container files
- Confluent/schema-registry envelope
- Avro JSON encoding
- schema evolution with separate writer/reader schemas

The model's generated schema is both the writer and reader schema in the default API.

## Schema generation

`model_avro_schema()` returns a fresh, clean, raw Avro schema dictionary.

`model_avro_schema_json()` returns the same schema as JSON text.

Schema generation is derived from Pydantic `model_fields` and resolved annotations. It is **not** converted from Pydantic JSON Schema and does not depend on Pydantic CoreSchema in v0.

Parsed `fastavro` schemas may be cached internally for encode/decode, but those parsed schemas are not exposed.

## Type mapping v0

| Python / Pydantic type | Avro type |
| --- | --- |
| `None` | `null` |
| `bool` | `boolean` |
| `int` | `long` |
| `float` | `double` |
| `str` | `string` |
| `bytes` | `bytes` |
| `list[T]` | `{"type": "array", "items": T}` |
| `dict[str, T]` | `{"type": "map", "values": T}` |
| `Enum` | `enum` |
| `AvroBaseModel` | `record` |
| `T | None` | nullable union |

`int` maps to Avro `long` by default. Explicit 32-bit integer annotations can come later.

## Explicit non-scope v0

Reject these with `AvroSchemaGenerationError`:

- arbitrary unions except nullable fields
- discriminated unions
- recursive models
- non-string map keys
- decimal
- date/time/datetime logical types
- constrained fields as Avro constraints
- default factories
- explicit defaults that are not valid Avro defaults
- schema changes implied by custom validators/serializers

## Defaults

Avro defaults are emitted only for:

- `None`
- `bool`
- `int`
- `float`
- `str`
- enum values

Other explicit defaults fail schema generation. Silent omission is avoided because Avro defaults affect compatibility semantics.

Nullable union ordering follows Avro default rules:

- default `None`: `['null', T]`, default `null`
- non-null default: `[T, 'null']`, default value
- no default: `['null', T]`, no default

## Names and aliases

Avro field names are external wire names.

Field-name selection:

1. Pydantic serialization alias, if present
2. Pydantic alias, if present
3. Python field name

`model_dump_avro()` serializes:

```python
self.model_dump(by_alias=True, mode="python")
```

`model_validate_avro()` decodes Avro wire names, translates them to Pydantic validation keys, then validates with normal Pydantic validation.

So Avro payloads still use Avro field names on the wire, including serialization aliases.

## Record names

Each `AvroBaseModel` becomes a named Avro record.

Defaults:

- record name: class name
- namespace: sanitized module path

Nested models are emitted as named records and referenced by name when repeated.

Config can override names:

```python
class User(AvroBaseModel):
    model_config = AvroConfigDict(
        avro_name="User",
        avro_namespace="com.example",
    )
```

## Avro config

Try v0 with a typed `ConfigDict` extension:

```python
from pydantic import ConfigDict


class AvroConfigDict(ConfigDict, total=False):
    avro_name: str
    avro_namespace: str
```

If this becomes expensive or fights Pydantic internals, pivot quickly to a separate `avro_config` class variable. Do not let config integration block v0.

## Codec

Use `fastavro` for schemaless binary encoding/decoding.

The library's value is Pydantic integration and Avro schema generation, not implementing an Avro codec.

## Errors

Library-owned failures are wrapped:

```python
class PydanticAvroError(Exception): ...
class AvroSchemaGenerationError(PydanticAvroError): ...
class AvroEncodeError(PydanticAvroError): ...
class AvroDecodeError(PydanticAvroError): ...
```

Underlying exceptions should be preserved with `raise ... from exc`.

Pydantic `ValidationError` from `model_validate_avro()` is not wrapped.

## Documentation metadata

- Model docstring maps to Avro record `doc`.
- Field `description` maps to Avro field `doc`.
- Field/model titles are ignored in v0.
- Non-standard Avro metadata is ignored in v0.

## Suggested package layout

```text
pydantic-avro/
  pyproject.toml
  README.md
  CONTEXT.md
  src/pydantic_avro/
    __init__.py
    base.py
    config.py
    errors.py
    schema.py
    codec.py
    conversion.py
  tests/
    test_base.py
    test_schema.py
    test_codec.py
```

## Open questions after v0

- `AvroTypeAdapter` for top-level arrays/maps/non-record types
- schema evolution APIs with separate writer/reader schemas
- Confluent/schema-registry support
- Avro object container files
- Avro JSON encoding
- logical types for decimal and temporal values
- explicit `AvroInt32()` / `AvroLong()` annotations
- custom field-level Avro metadata
