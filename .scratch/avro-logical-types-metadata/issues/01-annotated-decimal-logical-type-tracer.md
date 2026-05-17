# Annotated Decimal logical type tracer

Status: complete

## Parent

`.scratch/avro-logical-types-metadata/PRD.md`

## What to build

Add the first end-to-end Avro Metadata tracer: `Annotated[Decimal, AvroDecimal(...)]` should be public API, generate a bytes-backed Avro decimal logical type, remain fastavro-parseable, and round-trip through Avro Message encode/decode and normal Pydantic validation.

## Acceptance criteria

- [x] `AvroDecimal` is exported as public API and documented by tests as a keyword-only metadata helper.
- [x] `AvroDecimal` rejects invalid precision/scale values at construction time with normal Python value errors.
- [x] A Decimal field annotated with `AvroDecimal` emits Avro `bytes` with `logicalType: decimal`, `precision`, and `scale`.
- [x] Generated decimal schemas are fastavro-parseable.
- [x] Annotated Decimal values round-trip through Avro Message encode/decode and Pydantic validation.
- [x] Bare Decimal annotations fail schema generation with actionable guidance to use explicit decimal metadata.
- [x] Decimal defaults remain unsupported and fail schema generation clearly.

## Blocked by

None - can start immediately
