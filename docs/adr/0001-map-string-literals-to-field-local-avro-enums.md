# 0001 Map string Literals to field-local Avro enums

## Status

Accepted

## Context

Pydantic models can use `typing.Literal` to describe a closed vocabulary without defining a named `Enum` class. Avro has a native enum type that can preserve this closed vocabulary in the generated Avro Schema.

NeoDelta uses string Literals for fields such as `op_type` and `event_type`. Mapping those fields to unconstrained Avro strings would lose an important constraint at the Avro Schema boundary.

## Decision

Support string-only `Literal[...]` annotations as Avro enums.

Generated Literal Enum names are field-local for direct fields:

- direct field: `{ContainingRecordName}_{AvroFieldName}_Enum`

Nested models use their own containing record name, not the outer traversal path.

Nullable direct-field Literal Enums compose with existing nullable handling. Literal Enums inside containers are deferred and rejected for now. Single-value Literals are emitted as one-symbol Avro enums. Duplicate literal values are deduplicated preserving first occurrence.

Reject unsupported Literals at Avro Schema generation time:

- non-string literals
- invalid Avro enum symbols

Do not sanitize symbols. Do not merge same-shaped Literals across fields. Do not invent array-item or map-value enum names until real demand appears. If shared semantics are intended, users should define a named `Enum`.

## Consequences

Generated Avro Schemas preserve Pydantic Literal constraints for string vocabularies.

Schemas become stricter than plain string mappings, which is desired but may reject some existing models with non-Avro-compatible literal values.

The validation happens at Avro Schema generation time rather than static type-check time. Internally, parsing should convert annotations into a typed Literal Enum spec so later schema code cannot represent invalid Literal Enum states.

A helper alias/type for Avro enum literals may be added later, but v0 documents direct string `Literal[...]` support instead of adding a wrapper with weak static guarantees.
