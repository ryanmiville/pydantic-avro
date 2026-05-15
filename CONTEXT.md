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

**AvroConfigDict**:
A typed extension of Pydantic `ConfigDict` for Avro-specific model settings under `avro_`-prefixed keys.
_Avoid_: Separate avro_config unless model_config integration becomes costly

**PydanticAvroError**:
The base library exception for Avro schema generation, encoding, and decoding failures; Pydantic validation errors remain unchanged.
_Avoid_: Wrapping Pydantic ValidationError

## Relationships

- Public v0 exports are **AvroBaseModel**, **AvroConfigDict**, **PydanticAvroError**, **AvroSchemaGenerationError**, **AvroEncodeError**, and **AvroDecodeError**.
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
- Model docstrings map to Avro record `doc`; field descriptions map to Avro field `doc`; titles and non-standard metadata are ignored in v0.
- v0 rejects arbitrary unions, discriminated unions, constrained Avro constraints, decimal, temporal logical types, recursive models, non-string map keys, and schema changes from custom validators/serializers.
- An **Avro Message** is encoded and decoded with exactly one **Avro Schema** in the default API.
- An **Avro Schema** is derived from Pydantic `model_fields` and resolved annotations in v0, not converted from JSON Schema or generated from CoreSchema.
- `model_avro_schema()` returns a raw dictionary; parsed encoder/decoder schemas are internal cache details.
- An **Avro Field Name** is the key used in the Avro schema and Avro message payload.
- Decoded **Avro Message** data is validated by alias-only wire names, not Python field names.
- Decoded **Avro Message** data uses normal Pydantic validation, not forced strict mode.

## Example dialogue

> **Dev:** "Does `model_dump_avro()` return a string?"
> **Domain expert:** "No — an **Avro Message** is binary bytes for one record; use `model_avro_schema_json()` if you need a schema string."

## Flagged ambiguities

- "Avro message" was resolved to mean schemaless binary record bytes, not object container files, schema-registry envelopes, or Avro JSON encoding.
