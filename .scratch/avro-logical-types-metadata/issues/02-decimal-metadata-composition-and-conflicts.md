# Decimal metadata composition and conflicts

Status: complete

## Parent

`.scratch/avro-logical-types-metadata/PRD.md`

## What to build

Extend the Decimal Avro Metadata path so metadata attached through `Annotated[...]` behaves consistently in real model shapes: named aliases, nullable fields, arrays, and string-keyed maps. Non-Avro annotation metadata should coexist harmlessly, while duplicate, conflicting, or type-incompatible Avro Metadata should fail during Avro Schema generation.

## Acceptance criteria

- [x] Decimal Avro Metadata attached to a named alias applies wherever that alias is used.
- [x] Annotated Decimal logical types work in nullable fields.
- [x] Annotated Decimal logical types work inside arrays.
- [x] Annotated Decimal logical types work inside string-keyed maps.
- [x] Non-Avro `Annotated[...]` metadata is ignored by Avro Schema generation.
- [x] Duplicate or conflicting decimal metadata fails with `AvroSchemaGenerationError`.
- [x] Decimal metadata applied to an incompatible base annotation fails with `AvroSchemaGenerationError`.
- [x] Tests verify behavior through public schema generation and Avro Message APIs, not private parser shape.

## Blocked by

- `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
