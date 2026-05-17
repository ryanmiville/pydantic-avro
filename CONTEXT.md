# Pydantic Avro

Pydantic Avro maps Pydantic models to Avro's schema-driven binary record format.

## Language

**Avro Message**:
A single schemaless binary Avro record encoded using the model's generated Avro schema.
_Avoid_: Avro string, Avro file, container file, schema-registry message

**Avro Schema**:
A clean raw Avro schema dictionary generated from a Pydantic model and used as both the writer and reader schema in the default API.
_Avoid_: JSON Schema, Pydantic schema, parsed fastavro schema

**AvroBaseModel**:
The sole v0 public model base class for Avro schema generation and Avro message encode/decode.
_Avoid_: AvroTypeAdapter, standalone Avro functions

**Avro Field Name**:
The external record field name, chosen from Pydantic serialization alias if present, else alias, else Python field name.
_Avoid_: Always Python attribute name

**Avro Record Name**:
The Avro record identity for a model, defaulting to the class name within a sanitized module-path namespace.
_Avoid_: Anonymous nested records, duplicated inline records

**Literal Enum**:
A string `Literal[...]` annotation represented as an Avro enum so the Avro Schema preserves the same closed vocabulary as Pydantic validation.
_Avoid_: Treating string literals as unconstrained Avro strings, accepting numeric/bool/None literals as Avro enum symbols

**Avro Logical Type**:
An Avro primitive with standardized logical metadata that preserves a richer Python value type at the schema boundary.
_Avoid_: Custom field metadata, Pydantic serializer behavior, JSON Schema format

**Avro Metadata**:
Typed schema annotations that express Avro-specific choices not captured by the Python value type alone.
_Avoid_: Stringly-typed dictionaries, arbitrary JSON Schema extras, Pydantic-only metadata

**Anonymous Literal Enum**:
A plain string `Literal[...]` represented as a field-local Avro enum whose generated name uses `{ContainingRecordName}_{AvroFieldName}_Enum` for direct fields.
_Avoid_: Inferring the name from `OpType = Literal[...]`, merging same-shaped anonymous literals into one shared type

**Named Literal Enum**:
A Python named type alias, `type OpType = Literal[...]`, represented as an Avro enum named from the declared alias name.
_Avoid_: Using import aliases as Avro enum names, auto-disambiguating colliding Avro names

**AvroConfigDict**:
A typed extension of Pydantic `ConfigDict` for Avro-specific model settings under `avro_`-prefixed keys.
_Avoid_: Separate avro_config unless model_config integration becomes costly

**PydanticAvroError**:
The base library exception for Avro schema generation, encoding, and decoding failures; Pydantic validation errors remain unchanged.
_Avoid_: Wrapping Pydantic ValidationError

## Relationships

- Public v0 exports are **AvroBaseModel**, **AvroConfigDict**, **AvroDecimal**, **PydanticAvroError**, **AvroSchemaGenerationError**, **AvroEncodeError**, and **AvroDecodeError**.
- v0 supports Avro mappings for null, boolean, long, double, string, bytes, arrays, string-keyed maps, enums, records, and nullable fields.
- Python `int` maps to Avro `long` by default; explicit 32-bit integer annotations are deferred.
- Nullable fields order Avro union branches so the default value matches the first branch when a default exists.
- v0 emits Avro defaults for None, bool, int, float, str, and enum values; other explicit defaults and all default factories are rejected.
- Nested models are emitted as named **Avro Record Name** definitions and referenced by name when repeated.
- Avro model settings live in `model_config` via **AvroConfigDict** for v0; pivot quickly to a separate `avro_config` if this slows implementation.
- v0 uses `fastavro` for schemaless binary encoding and decoding.
- `model_dump_avro()` serializes `model_dump(by_alias=True, mode="python")` through `fastavro`.
- `model_avro_schema()` returns a freshly generated raw dictionary; parsed `fastavro` schemas may be cached internally for encode/decode.
- v0 wraps schema, encode, and decode failures in **PydanticAvroError** subclasses while preserving Pydantic `ValidationError` unchanged.
- Model docstrings map to Avro record `doc`; field descriptions are the canonical surface for Avro field `doc`; titles and non-standard metadata are ignored in v0.
- v0 rejects arbitrary unions, discriminated unions, constrained Avro constraints, decimal, temporal logical types, recursive models, non-string map keys, and schema changes from custom validators/serializers.
- **Avro Logical Types** are inferred from standard Python value types when there is one obvious Avro mapping; under-specified logical types require explicit Avro metadata.
- Python `datetime` maps to Avro `timestamp-micros`; local timestamp semantics are not inferred from plain `datetime`.
- Encoding a Python `datetime` as `timestamp-micros` requires a timezone-aware value because Avro stores a UTC instant and does not preserve local timezone identity.
- Decoding Avro `timestamp-micros` returns the UTC-aware `datetime` representation of the stored instant.
- Python `time` maps to Avro `time-micros` to preserve microsecond precision.
- Python `UUID` maps to Avro `string` with UUID logical metadata; plain `str` remains a plain Avro string.
- Python `Decimal` requires explicit keyword-only **Avro Metadata** for precision and scale and maps to bytes-backed decimal unless fixed-backed decimal support is added later.
- Avro defaults are supported for temporal and UUID logical types; decimal logical defaults are deferred.
- Datetime logical defaults must be timezone-aware for the same reason as datetime message values.
- Logical type schema defaults are emitted as Avro's underlying primitive JSON values.
- Decimal value precision and scale are enforced by the Avro codec during message encoding, not reimplemented by Pydantic Avro.
- Calendar-date logical values reject `datetime` values where a pure `date` is required.
- **Avro Metadata** helper objects validate their own values when constructed; invalid helper values raise normal Python value errors.
- **Avro Metadata** is represented by specific typed helper objects rather than generic dictionaries.
- **Avro Metadata** does not duplicate Pydantic surfaces that already map cleanly to Avro, such as field aliases for Avro field names and field descriptions for Avro field `doc`.
- Pydantic JSON Schema-only metadata, including field titles and `json_schema_extra`, is ignored for Avro schema generation.
- Avro-specific metadata is supplied only through `Annotated[...]` helper objects.
- Pydantic `Field(...)` metadata may be written inside or outside `Annotated[...]`; Avro schema generation reads normalized Pydantic field info and only parses Avro helper objects from `Annotated[...]` metadata.
- Non-Avro `Annotated[...]` metadata is ignored by Avro schema generation.
- Duplicate, conflicting, or type-incompatible **Avro Metadata** is rejected during Avro schema generation.
- **Avro Metadata** attached to named aliases applies consistently anywhere that alias is used, including inside containers.
- Supported logical types compose through nullable fields, arrays, and string-keyed maps.
- Logical type inference recognizes the exact supported standard-library annotations, not Pydantic constrained types or subclass annotations.
- An **Avro Message** is encoded and decoded with exactly one **Avro Schema** in the default API.
- An **Avro Schema** is derived from Pydantic `model_fields` and resolved annotations in v0, not converted from JSON Schema or generated from CoreSchema.
- `model_avro_schema()` returns a raw dictionary; parsed encoder/decoder schemas are internal cache details.
- An **Avro Field Name** is the key used in the Avro schema and Avro message payload.
- Decoded **Avro Message** data comes from Avro wire names and is translated to Pydantic validation keys before normal validation.
- Decoded **Avro Message** data uses normal Pydantic validation, not forced strict mode.

## Example dialogue

> **Dev:** "Does `model_dump_avro()` return a string?"
> **Domain expert:** "No — an **Avro Message** is binary bytes for one record; use `model_avro_schema_json()` if you need a schema string."

## Flagged ambiguities

- "Avro message" was resolved to mean schemaless binary record bytes, not object container files, schema-registry envelopes, or Avro JSON encoding.
- A dedicated helper alias/type for Avro enum literals is deferred; Python named type aliases are the canonical way to name **Named Literal Enums**.
