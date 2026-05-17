# Annotated Avro metadata

Status: needs-triage

## What to build

Add typed `Annotated[...]` metadata objects for Avro-specific schema choices that Pydantic annotations cannot express directly, such as logical-type parameters, names, aliases, docs, fixed sizes, and numeric representation hints.

## Acceptance criteria

- [ ] Public metadata helper types are exported and documented.
- [ ] `Annotated[T, ...]` metadata participates in schema generation instead of being silently discarded.
- [ ] Logical-type knobs such as decimal precision/scale can be represented without stringly-typed dicts.
- [ ] Conflicting metadata is rejected with clear `AvroSchemaGenerationError` messages.

## Resolved design

- Avro-specific metadata is supplied only through typed `Annotated[...]` helper objects.
- First public helper is `AvroDecimal`; do not add `AvroDate`, `AvroTime`, `AvroTimestamp`, `AvroUUID`, `AvroDoc`, or `AvroAliases` in this slice.
- Reuse Pydantic `Field` attributes when they clearly translate to Avro:
  - `alias` / `serialization_alias` -> Avro field name
  - `description` -> Avro field `doc`
  - supported defaults -> Avro defaults
- Ignore JSON Schema-only metadata such as `title`, `examples`, and `json_schema_extra`; do not treat it as Avro metadata and do not police Avro-looking keys inside it.
- Pydantic `Field(...)` may be written inside or outside `Annotated[...]`; schema generation reads normalized Pydantic field info and only parses Avro helper objects from `Annotated[...]` metadata.
- Ignore non-Avro `Annotated[...]` metadata.
- Reject duplicate, conflicting, or type-incompatible Avro helper metadata with `AvroSchemaGenerationError`.
- Metadata attached to named aliases applies consistently anywhere that alias is used, including nullable fields, arrays, and string-keyed maps.
- Record-level naming remains in `AvroConfigDict`; do not add competing `Annotated` record-name metadata yet.

## Blocked by

- `.scratch/avro-feature-roadmap/issues/01-logical-types.md`
