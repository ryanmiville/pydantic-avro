# Logical type docs and roadmap cleanup

Status: complete

## Parent

`.scratch/avro-logical-types-metadata/PRD.md`

## What to build

Document the completed Avro Logical Type and Avro Metadata behavior from a user's perspective. The docs should explain inferred logical mappings, explicit Decimal metadata, Pydantic Field reuse, ignored JSON Schema-only metadata, and deferred features so future users and agents do not infer competing API surfaces.

## Acceptance criteria

- [x] Documentation lists supported inferred Avro Logical Types and their Avro primitive/logical mappings.
- [x] Documentation shows `Annotated[Decimal, AvroDecimal(precision=..., scale=...)]` as the Decimal surface.
- [x] Documentation explains that bare Decimal is under-specified and rejected.
- [x] Documentation explains timezone-aware datetime requirements and UTC-aware timestamp decode behavior.
- [x] Documentation explains that Pydantic aliases, descriptions, and supported defaults are reused for Avro when they clearly translate.
- [x] Documentation explains that JSON Schema-only metadata such as title, examples, and `json_schema_extra` is ignored for Avro generation.
- [x] Documentation names deferred features: local timestamps, millis knobs, fixed-backed decimal, decimal defaults, Avro doc/alias helpers, and record-name metadata helpers.
- [x] Roadmap issue status/details are consistent with the implemented behavior.

## Blocked by

- `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
- `.scratch/avro-logical-types-metadata/issues/02-decimal-metadata-composition-and-conflicts.md`
- `.scratch/avro-logical-types-metadata/issues/03-date-time-and-uuid-logical-types.md`
- `.scratch/avro-logical-types-metadata/issues/04-timestamp-logical-type-with-timezone-safety.md`
