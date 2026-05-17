# Avro feature roadmap

## Priority order

1. Issue 01: Logical types — first slice complete: date, time-micros, timestamp-micros, uuid, and bytes-backed decimal via `Annotated[Decimal, AvroDecimal(...)]`
2. Issue 02: Annotated support for Avro types/metadata — first slice complete for `AvroDecimal`; broader helper surfaces deferred
3. Issue 04: Confluent/schema-registry format
4. Issue 05: Arbitrary unions
5. Issue 06: Recursive models

## Notes

- Logical types and `Annotated` metadata should share a design surface.
- Scope excludes compatibility checking, schema diff UX, and code-generation CLIs.
