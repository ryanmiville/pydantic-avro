# pydantic-avro v0 implementation plan

This plan is written for a fresh implementation agent. Read `CONTEXT.md` and `README.md` first; they define the domain language and settled product decisions.

## Goal

Implement v0 of `pydantic-avro`: a small Pydantic v2 integration that provides `AvroBaseModel` with:

```python
class User(AvroBaseModel):
    id: int
    name: str

schema: dict[str, Any] = User.model_avro_schema()
schema_json: str = User.model_avro_schema_json()
payload: bytes = User(id=1, name="Ada").model_dump_avro()
user: User = User.model_validate_avro(payload)
```

v0 only supports one schemaless binary Avro record encoded/decoded with the model's own generated schema. Use `fastavro`; do not implement Avro encoding manually.

## Non-goals

Do not implement in v0:

- Avro object container files
- Confluent/schema-registry wire format
- Avro JSON encoding
- separate writer/reader schemas or schema evolution APIs
- top-level `AvroTypeAdapter`
- standalone dump/validate functions
- arbitrary unions except nullable `T | None`
- recursive models
- decimal/date/time/datetime logical types
- constrained fields as Avro constraints
- non-string map keys
- default factories
- custom validators/serializers affecting schema

Reject unsupported schema features with `AvroSchemaGenerationError`.

## Package layout

Create:

```text
pyproject.toml
README.md                  # already exists; preserve/update as needed
CONTEXT.md                 # already exists; preserve/update as decisions change
IMPLEMENTATION_PLAN.md     # this file
src/pydantic_avro/
  __init__.py
  base.py
  codec.py
  config.py
  errors.py
  schema.py
  typing.py               # optional helper types if useful
tests/
  test_base.py
  test_codec.py
  test_errors.py
  test_schema.py
```

Use `src` layout.

## Dependencies

Runtime:

- `pydantic>=2`
- `fastavro`

Dev/test:

- `pytest`
- `mypy` or `pyright` optional, if project tooling is added
- `ruff` optional

Use modern `pyproject.toml` with PEP 621 metadata.

## Public API

`src/pydantic_avro/__init__.py` should export:

```python
from .base import AvroBaseModel
from .config import AvroConfigDict
from .errors import (
    PydanticAvroError,
    AvroSchemaGenerationError,
    AvroEncodeError,
    AvroDecodeError,
)

__all__ = (
    "AvroBaseModel",
    "AvroConfigDict",
    "PydanticAvroError",
    "AvroSchemaGenerationError",
    "AvroEncodeError",
    "AvroDecodeError",
)
```

## Config

Implement `AvroConfigDict` as a typed extension of Pydantic's `ConfigDict`:

```python
from pydantic import ConfigDict

class AvroConfigDict(ConfigDict, total=False):
    avro_name: str
    avro_namespace: str
```

Use `model_config`:

```python
class User(AvroBaseModel):
    model_config = AvroConfigDict(avro_namespace="com.example")
```

Implementation should read with:

```python
cls.model_config.get("avro_name")
cls.model_config.get("avro_namespace")
```

If this fights Pydantic or type checking, pivot quickly to separate `avro_config`. Do not spend much time fighting this.

## Errors

Implement:

```python
class PydanticAvroError(Exception): ...
class AvroSchemaGenerationError(PydanticAvroError): ...
class AvroEncodeError(PydanticAvroError): ...
class AvroDecodeError(PydanticAvroError): ...
```

Rules:

- Wrap schema generation problems in `AvroSchemaGenerationError`.
- Wrap fastavro encode problems in `AvroEncodeError`.
- Wrap fastavro decode problems in `AvroDecodeError`.
- Preserve original cause: `raise AvroEncodeError(...) from exc`.
- Do **not** wrap Pydantic `ValidationError` from `model_validate_avro()`.

## `AvroBaseModel`

`base.py`:

```python
from __future__ import annotations

import io
import json
from typing import Any, Self

from pydantic import BaseModel

from .codec import decode_avro, encode_avro, get_parsed_schema
from .schema import generate_avro_schema

class AvroBaseModel(BaseModel):
    @classmethod
    def model_avro_schema(cls) -> dict[str, Any]: ...

    @classmethod
    def model_avro_schema_json(cls) -> str: ...

    @classmethod
    def model_validate_avro(cls, data: bytes | bytearray | memoryview) -> Self: ...

    def model_dump_avro(self) -> bytes: ...
```

Behavior:

### `model_avro_schema()`

- Return a fresh raw `dict[str, Any]` each call.
- Do not return fastavro's parsed schema.
- Generate from Pydantic `model_fields` and annotations.
- If unsupported, raise `AvroSchemaGenerationError`.

### `model_avro_schema_json()`

- Return `json.dumps(cls.model_avro_schema())`.
- Use stable output if convenient: `separators=(",", ":")` or `indent=2`; choose one and test exact only if needed.

### `model_dump_avro()`

- Generate/get parsed schema for class.
- Dump model data with:

```python
record = self.model_dump(by_alias=True, mode="python")
```

- Encode with `fastavro.schemaless_writer` into `bytes`.
- Wrap encode errors in `AvroEncodeError`.

### `model_validate_avro()`

- Decode bytes with the class schema using `fastavro.schemaless_reader`.
- Then validate with:

```python
return cls.model_validate(decoded, by_alias=True, by_name=False)
```

- Wrap fastavro decode errors in `AvroDecodeError`.
- Let Pydantic `ValidationError` bubble unchanged.

Input type should be bytes-like. Reject non-bytes-like input with `AvroDecodeError` or `TypeError`; prefer `AvroDecodeError` for public consistency.

## Codec layer

`codec.py` responsibilities:

- parse raw schema with `fastavro.parse_schema`
- encode one schemaless record
- decode one schemaless record
- optionally cache parsed schema per model class

Suggested functions:

```python
from typing import Any, Type
from weakref import WeakKeyDictionary

from fastavro import parse_schema, schemaless_reader, schemaless_writer

_PARSED_SCHEMA_CACHE: WeakKeyDictionary[type, dict[str, Any]] = WeakKeyDictionary()


def get_parsed_schema(model_cls: type[AvroBaseModel]) -> dict[str, Any]: ...
def encode_avro(parsed_schema: dict[str, Any], record: dict[str, Any]) -> bytes: ...
def decode_avro(parsed_schema: dict[str, Any], data: bytes | bytearray | memoryview) -> dict[str, Any]: ...
```

Avoid circular imports by using `TYPE_CHECKING` or accepting `type[Any]`.

Caching:

- `model_avro_schema()` fresh raw dict each call.
- `get_parsed_schema()` may cache fastavro parsed schema internally.
- Cache key can be model class.
- If model classes are rebuilt dynamically, cache invalidation may be needed later; ignore unless tests expose issue.

Encoding:

```python
buf = io.BytesIO()
schemaless_writer(buf, parsed_schema, record)
return buf.getvalue()
```

Decoding:

```python
buf = io.BytesIO(bytes(data))
return schemaless_reader(buf, parsed_schema)
```

## Schema generation

`schema.py` is the core.

### Public-ish function

```python
def generate_avro_schema(model_cls: type[AvroBaseModel]) -> dict[str, Any]: ...
```

It should raise `AvroSchemaGenerationError` for unsupported types.

### Generator state

Use an internal generator class to track named records/enums and prevent duplication:

```python
@dataclass
class SchemaGenerator:
    names: dict[type[Any], str]
    definitions: dict[str, dict[str, Any]]
    visiting: set[type[Any]]
```

But Avro schemas do not have `$defs`. Named records are usually introduced inline once; later references can be by full name string. So generation needs to produce a root record where nested named records appear inline at first reference and later as full-name strings.

Simpler v0 approach:

- Maintain `emitted_names: set[str]`.
- When generating a model record:
  - compute full name
  - if currently visiting same model: reject recursive model
  - if full name already emitted: return full name string reference
  - else mark emitted and emit full record dict inline

This handles repeated nested model references without duplicating full definitions.

### Record naming

For a model class:

- `name = model_config.get("avro_name") or cls.__name__`
- `namespace = model_config.get("avro_namespace") or sanitize_module(cls.__module__)`
- full name = `f"{namespace}.{name}"` if namespace else name

Sanitization:

- Avro names: `[A-Za-z_][A-Za-z0-9_]*`
- Namespace is dot-separated names.
- Module path may include invalid chars; replace invalid chars with `_`.
- If segment starts with digit, prefix `_`.
- Consider dropping `__main__` or mapping it to `main`; choose deterministic behavior and test it.

Record schema shape:

```python
{
    "type": "record",
    "name": name,
    "namespace": namespace,
    "doc": cleaned_docstring,  # if present
    "fields": [...],
}
```

Docstring:

- Use `inspect.getdoc(cls)`.
- Ignore if absent.
- Probably ignore BaseModel inherited docstring by checking `cls.__doc__`? Simpler: if `inspect.getdoc(cls)` exists and class defines docstring, use it.

### Field generation

Iterate `model_cls.model_fields.items()`.

For each field:

- determine Avro field name
- determine Avro type
- determine Avro default if any
- map description to `doc`

Field name priority:

1. `field.serialization_alias`
2. `field.alias`
3. Python field name

Implementation note: Pydantic `FieldInfo` attributes may be `None`. Inspect with a quick local test if uncertain.

Field dict:

```python
field_schema = {
    "name": avro_field_name,
    "type": avro_type,
}
if description:
    field_schema["doc"] = description
if has_supported_default:
    field_schema["default"] = avro_default
```

### Required/default detection

Pydantic field info has methods/attributes such as `is_required()`, `default`, `default_factory`.

Rules:

- If `default_factory` present: reject.
- If required: no Avro default.
- If explicit default is supported: emit default.
- If explicit default unsupported: reject.

Supported defaults:

- `None`
- `bool`
- `int`
- `float`
- `str`
- enum instance -> enum value/name string according to enum schema representation

Do not support bytes default in v0.

### Type mapping

Implement a recursive function:

```python
def avro_type_for_annotation(annotation: Any, *, default: Any = PydanticUndefined) -> AvroType: ...
```

Use `typing.get_origin`, `typing.get_args`, `types.UnionType` support.

Supported mappings:

#### None

`None` / `NoneType` -> `"null"`

#### bool

`bool` -> `"boolean"`

Important: check `bool` before `int` because `bool` is a subclass of `int` in Python.

#### int

`int` -> `"long"`

Do not infer Avro `int` from constraints in v0.

#### float

`float` -> `"double"`

#### str

`str` -> `"string"`

#### bytes

`bytes` -> `"bytes"`

#### list[T]

Support `list[T]`, `typing.List[T]`, and likely `collections.abc.Sequence[T]` only if trivial. Prefer just `list[T]` for v0.

```python
{"type": "array", "items": avro_type(T)}
```

Reject unparameterized `list` unless choosing `items: "string"`/`"null"`; recommended: reject unparameterized containers.

#### dict[str, T]

Support `dict[str, T]`.

```python
{"type": "map", "values": avro_type(T)}
```

Reject non-string keys and unparameterized dicts.

#### Enum

Support subclasses of `enum.Enum`.

Avro enum schema:

```python
{
    "type": "enum",
    "name": enum_cls.__name__,
    "namespace": sanitize_module(enum_cls.__module__),
    "symbols": [...],
}
```

Symbol choice:

- Use enum values if all values are strings and valid Avro symbols.
- Otherwise use enum member names.
- Defaults for enum fields must use the same symbol representation.

Validate symbols against Avro name rules. Reject invalid symbols with `AvroSchemaGenerationError`.

Like records, emit enum schema first time and full-name reference on repeats.

#### AvroBaseModel nested records

Support nested `AvroBaseModel` subclasses.

```python
class Address(AvroBaseModel): ...
class User(AvroBaseModel):
    address: Address
```

`User.model_avro_schema()` should include `Address` as an inline named record at first reference. If `Address` appears again, use full-name string reference.

Reject direct/indirect recursion:

```python
class Node(AvroBaseModel):
    child: Node | None
```

#### Optional / nullable

Support only unions of exactly one non-null type and null:

- `T | None`
- `None | T`
- `typing.Optional[T]`
- `typing.Union[T, None]`

Reject all other unions.

Union ordering:

- default `None`: `["null", T]`, default `None`
- non-null default: `[T, "null"]`, default value
- no default: `["null", T]`, no default

The field generation layer likely has default info, so nullable ordering may need both annotation and field default.

### Unsupported annotations

Reject with actionable messages, e.g.:

```text
Unsupported Avro type for field 'created_at': datetime.datetime is not supported in v0; temporal logical types are deferred.
```

Include field path for nested failures where possible:

```text
Unsupported Avro type for field 'addresses[].zip': ...
```

Do not over-engineer field paths if it slows v0; at least include top-level field name.

## Avro schema validation with fastavro

After generating raw schema, run `fastavro.parse_schema(schema)` in codec path. This catches malformed Avro schema.

For `model_avro_schema()`, decide whether to validate immediately:

- Recommended: yes, call `parse_schema` on generated schema and wrap parse errors in `AvroSchemaGenerationError`, but return the raw schema.
- This guarantees public schema output is valid Avro.

Avoid returning parse markers from fastavro.

## Tests

Write semantic tests. Avoid tests that only assert implementation details.

### `test_schema.py`

1. Primitive record schema:

```python
class User(AvroBaseModel):
    id: int
    name: str
    active: bool
```

Assert schema has record name, fields, and `int -> long`.

2. Optional field with default `None`:

```python
email: str | None = None
```

Assert type `['null', 'string']`, default `None`.

3. Optional field with non-null default:

```python
nickname: str | None = "anon"
```

Assert type `['string', 'null']`, default `"anon"`.

4. Alias behavior:

```python
user_id: int = Field(serialization_alias="userId")
```

Assert Avro field name is `userId`.

5. Description/doc behavior:

- model docstring -> record `doc`
- field description -> field `doc`

6. Nested model:

```python
class Address(AvroBaseModel): ...
class User(AvroBaseModel):
    home: Address
    work: Address
```

Assert first nested field has record schema and second references full name.

7. Enum:

```python
class Color(str, Enum):
    RED = "RED"
```

Assert enum schema and roundtrip default if applicable.

8. Unsupported union fails.

9. Default factory fails.

10. Non-string dict key fails.

11. Complex default fails.

12. `model_avro_schema()` returns a fresh dict: mutate first result, call again, assert unaffected.

### `test_codec.py`

1. Roundtrip primitive model:

```python
payload = user.model_dump_avro()
assert isinstance(payload, bytes)
assert User.model_validate_avro(payload) == user
```

2. Roundtrip nested model.

3. Roundtrip alias field; decoded Avro uses alias but model has Python attr.

4. Invalid bytes raise `AvroDecodeError`.

5. Encode failure wraps `AvroEncodeError` if possible. One way: monkeypatch codec function or construct bad record via internal function. Avoid brittle fastavro behavior if hard.

6. Pydantic `ValidationError` is not wrapped. This may be hard because Avro decode usually conforms to schema. Can monkeypatch `decode_avro` to return invalid dict, or test via a validator that rejects decoded value.

Example:

```python
class Model(AvroBaseModel):
    x: int

    @field_validator("x")
    def reject_one(cls, v):
        if v == 1: raise ValueError("bad")
        return v
```

Encode `x=1` may fail because model cannot be constructed. Instead use fastavro directly to encode invalid business value or use a validator condition on valid construction path carefully. If too awkward, skip until implementation has hooks.

### `test_base.py`

1. API methods exist and signatures roughly right.
2. `model_avro_schema_json()` is valid JSON and equals `model_avro_schema()` after `json.loads`.
3. `AvroConfigDict` name/namespace override works.

### `test_errors.py`

1. Unsupported type raises `AvroSchemaGenerationError` with field name.
2. Bad decode input raises `AvroDecodeError`.
3. Public exceptions inherit from `PydanticAvroError`.

## Implementation order

1. Create project skeleton and `pyproject.toml`.
2. Add exceptions and public exports.
3. Add `AvroBaseModel` stubs.
4. Implement primitive schema generation.
5. Add first schema tests.
6. Implement codec with `fastavro`.
7. Add primitive roundtrip tests.
8. Implement aliases and docs.
9. Implement optional/default rules.
10. Implement lists and maps.
11. Implement nested records and duplicate named references.
12. Implement enums.
13. Add unsupported-type errors and tests.
14. Add parsed schema caching if needed.
15. Run full tests and update README if behavior differs.

## Design constraints

- Keep v0 small. Prefer explicit `AvroSchemaGenerationError` over partial/incorrect support.
- Do not convert from JSON Schema.
- Do not depend on Pydantic CoreSchema in v0.
- Do not expose fastavro parsed schemas.
- Do not wrap Pydantic `ValidationError`.
- Prefer boring code over clever abstractions.

## Useful local references

In the sibling `~/dev/pydantic` repo, relevant concepts are documented in:

- `docs/internals/architecture.md` — Pydantic v2 schema/validator/serializer architecture.
- `docs/concepts/json.md` — JSON parse/dump behavior.
- `docs/concepts/json_schema.md` — JSON Schema is a projection from Pydantic's internal schema.
- `docs/concepts/alias.md` — alias behavior. Validation aliases default on; serialization aliases default off unless requested.

The pydantic-avro decisions intentionally mimic Pydantic where useful, but Avro is treated as an external wire contract, so aliases are always used for Avro payload names in v0.
