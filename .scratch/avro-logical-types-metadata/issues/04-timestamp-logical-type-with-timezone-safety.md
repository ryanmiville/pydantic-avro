# Timestamp logical type with timezone safety

Status: ready-for-agent

## Parent

`.scratch/avro-logical-types-metadata/PRD.md`

## What to build

Add inferred Avro `timestamp-micros` support for exact standard-library `datetime` annotations, with explicit timezone safety at Avro boundaries. Timestamp values should encode only when timezone-aware, decode as the codec's UTC-aware representation, compose through existing nullable/container support, and emit deterministic primitive defaults.

## Acceptance criteria

- [ ] `datetime` annotations emit Avro `long` with `logicalType: timestamp-micros`.
- [ ] Generated timestamp schemas are fastavro-parseable.
- [ ] Timezone-aware datetime values round-trip through Avro Message encode/decode and Pydantic validation.
- [ ] Decoded timestamp values preserve the UTC-aware datetime representation of the stored instant.
- [ ] Naive datetime values fail Avro Message encoding with a clear Avro encode failure.
- [ ] Naive datetime defaults fail Avro Schema generation with a clear schema generation error.
- [ ] Timestamp defaults emit Avro's underlying primitive JSON value.
- [ ] Timestamp logical types compose through nullable fields, arrays, and string-keyed maps.
- [ ] Local timestamp semantics are not inferred from plain `datetime`.

## Blocked by

- `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
