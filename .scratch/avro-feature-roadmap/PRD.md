# Avro feature roadmap

## Priority order

1. Logical types — first slice complete: date, time-micros, timestamp-micros, uuid, and bytes-backed decimal via `Annotated[Decimal, AvroDecimal(...)]`
2. Annotated support for Avro types/metadata — first slice complete for `AvroDecimal`; broader helper surfaces deferred
3. Compatibility checker
4. Confluent/schema-registry format
5. Arbitrary unions
6. Recursive models
7. Avro schema JSON to Pydantic CLI
8. Pydantic model to Avro schema CLI
9. Schema diff UX

## Notes

- Logical types and `Annotated` metadata should share a design surface.
- Compatibility semantics should follow Avro reader/writer schema resolution.
- Recursive models are higher priority than CLI generation work.
