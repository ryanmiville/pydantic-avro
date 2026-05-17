# Date, time, and UUID logical types

Status: ready-for-agent

## Parent

`.scratch/avro-logical-types-metadata/PRD.md`

## What to build

Add inferred Avro Logical Types for exact standard-library date, time, and UUID annotations. These types should generate spec-compatible raw Avro Schemas, compose through existing nullable/container support, round-trip through Avro Messages, and emit Avro primitive defaults where supported.

## Acceptance criteria

- [ ] `date` annotations emit Avro `int` with `logicalType: date`.
- [ ] `time` annotations emit Avro `long` with `logicalType: time-micros`.
- [ ] `UUID` annotations emit Avro `string` with `logicalType: uuid`.
- [ ] Plain `str` remains a plain Avro string and does not infer UUID semantics.
- [ ] Generated date, time, and UUID schemas are fastavro-parseable.
- [ ] Date, time, and UUID values round-trip through Avro Message encode/decode and Pydantic validation.
- [ ] Date, time, and UUID logical types compose through nullable fields, arrays, and string-keyed maps.
- [ ] Date, time, and UUID defaults emit Avro's underlying primitive JSON values.
- [ ] Calendar-date defaults reject `datetime` values where a pure date is required.

## Blocked by

- `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
