# Date, time, and UUID logical types

Status: complete

## Parent

`.scratch/avro-logical-types-metadata/PRD.md`

## What to build

Add inferred Avro Logical Types for exact standard-library date, time, and UUID annotations. These types should generate spec-compatible raw Avro Schemas, compose through existing nullable/container support, round-trip through Avro Messages, and emit Avro primitive defaults where supported.

## Acceptance criteria

- [x] `date` annotations emit Avro `int` with `logicalType: date`.
- [x] `time` annotations emit Avro `long` with `logicalType: time-micros`.
- [x] `UUID` annotations emit Avro `string` with `logicalType: uuid`.
- [x] Plain `str` remains a plain Avro string and does not infer UUID semantics.
- [x] Generated date, time, and UUID schemas are fastavro-parseable.
- [x] Date, time, and UUID values round-trip through Avro Message encode/decode and Pydantic validation.
- [x] Date, time, and UUID logical types compose through nullable fields, arrays, and string-keyed maps.
- [x] Date, time, and UUID defaults emit Avro's underlying primitive JSON values.
- [x] Calendar-date defaults reject `datetime` values where a pure date is required.

## Blocked by

- `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
