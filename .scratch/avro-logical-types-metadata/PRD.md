# Avro logical types and typed metadata

Status: complete

## Problem Statement

Pydantic Avro currently maps common Python value types to plain Avro primitives, which loses important Avro Schema semantics for dates, times, timestamps, UUIDs, and decimals. Users also have no type-safe way to express Avro-specific schema choices that Pydantic annotations cannot represent directly, so under-specified logical types such as decimal precision and scale cannot be modeled without adding stringly or JSON Schema-oriented escape hatches.

## Solution

Add first-class Avro Logical Type support and a small typed Avro Metadata surface. Obvious Python value types should infer their Avro Logical Type automatically, while under-specified logical types use typed `Annotated[...]` helper objects. Reuse existing Pydantic `Field` attributes when they clearly translate to Avro, and keep Avro-specific choices out of JSON Schema-only metadata.

## User Stories

1. As a Pydantic Avro user, I want a `date` field to generate an Avro `date` logical type, so that the Avro Schema preserves calendar-date semantics.
2. As a Pydantic Avro user, I want a `time` field to generate Avro `time-micros`, so that microsecond precision is not silently truncated.
3. As a Pydantic Avro user, I want a `datetime` field to generate Avro `timestamp-micros`, so that timestamps represent UTC instants on the wire.
4. As a Pydantic Avro user, I want timezone-aware datetimes to encode predictably, so that local machine timezone settings do not change Avro Messages.
5. As a Pydantic Avro user, I want naive datetimes rejected during Avro encoding, so that ambiguous timestamp values fail clearly.
6. As a Pydantic Avro user, I want naive datetime defaults rejected during Avro Schema generation, so that schema defaults are deterministic.
7. As a Pydantic Avro user, I want decoded Avro timestamps to validate through Pydantic as UTC-aware datetimes, so that the decoded model reflects the stored instant.
8. As a Pydantic Avro user, I want a `UUID` field to generate Avro `uuid`, so that Avro consumers understand the field is not an arbitrary string.
9. As a Pydantic Avro user, I want plain `str` fields to remain plain Avro strings, so that UUID semantics are only inferred from `UUID` annotations.
10. As a Pydantic Avro user, I want decimal fields to require explicit precision and scale, so that generated Avro decimal schemas are valid and intentional.
11. As a Pydantic Avro user, I want `AvroDecimal` to be typed and discoverable, so that I do not need stringly-typed dictionaries for decimal metadata.
12. As a Pydantic Avro user, I want invalid decimal metadata to fail when the helper object is constructed, so that impossible metadata is caught early.
13. As a Pydantic Avro user, I want decimal values to round-trip through Avro Messages, so that monetary and precise numeric values survive encode/decode.
14. As a Pydantic Avro user, I want logical types to compose through nullable fields, arrays, and string-keyed maps, so that nested value shapes work consistently.
15. As a Pydantic Avro user, I want Avro Metadata attached to a named alias to apply everywhere the alias is used, so that domain value aliases stay consistent.
16. As a Pydantic Avro user, I want duplicate Avro Metadata to fail clearly, so that conflicting schema instructions cannot be silently chosen by order.
17. As a Pydantic Avro user, I want type-incompatible Avro Metadata to fail clearly, so that invalid schema combinations do not reach the codec.
18. As a Pydantic Avro user, I want non-Avro `Annotated[...]` metadata ignored, so that Pydantic Avro can coexist with other annotation consumers.
19. As a Pydantic Avro user, I want Pydantic `Field(description=...)` to remain the source of Avro field `doc`, so that there is not a duplicate Avro documentation API.
20. As a Pydantic Avro user, I want Pydantic field aliases to remain the source of Avro Field Names, so that naming is controlled by one familiar surface.
21. As a Pydantic Avro user, I want JSON Schema-only metadata ignored for Avro generation, so that `title`, `examples`, and `json_schema_extra` keep their Pydantic meaning.
22. As a Pydantic Avro user, I want generated logical type schemas to remain fastavro-parseable, so that schema generation catches invalid Avro output.
23. As a Pydantic Avro user, I want supported logical type defaults emitted in Avro's primitive JSON representation, so that schemas remain spec-compatible.
24. As a Pydantic Avro user, I want decimal defaults deferred, so that the first implementation avoids ambiguous bytes-default encoding behavior.
25. As a library maintainer, I want a parser that keeps base annotations and Avro Metadata together, so that later schema code cannot accidentally discard metadata.
26. As a library maintainer, I want Avro Logical Type support implemented through public behavior tests, so that internal parser refactors do not break tests unnecessarily.
27. As an Avro consumer, I want generated schemas to distinguish logical values from their primitive storage types, so that downstream systems can apply Avro reader semantics.
28. As a future implementer, I want local timestamp, fixed-backed decimal, and additional Avro metadata surfaces deferred, so that the first slice remains small and coherent.

## Implementation Decisions

- Build a deep Avro Metadata parsing module that accepts a Python annotation and returns the effective base annotation plus recognized Avro helper metadata.
- The metadata parser must preserve `Annotated[...]` metadata instead of blindly unwrapping it, including metadata carried through named aliases.
- The first public Avro Metadata helper is `AvroDecimal`.
- `AvroDecimal` is a frozen, keyword-only value object with `precision` and `scale` fields.
- `AvroDecimal` validates `precision > 0`, `scale >= 0`, and `scale <= precision` during construction with normal Python value errors.
- Bare `Decimal` is under-specified and fails Avro Schema generation with guidance to use explicit decimal metadata.
- Decimal support emits bytes-backed Avro decimal schemas first; fixed-backed decimal is deferred.
- Decimal value precision and scale enforcement is delegated to the Avro codec during Avro Message encoding and wrapped as an Avro encode failure when it fails.
- Exact standard-library annotations infer obvious Avro Logical Types: calendar date, microsecond time, UTC timestamp, and UUID.
- Pydantic constrained temporal types, subclass annotations, and non-standard temporal annotations are out of scope for this slice.
- `datetime` maps to Avro `timestamp-micros`, not local timestamp semantics.
- Encoding timestamp logical values requires timezone-aware Python datetimes.
- Decoded timestamp logical values preserve the codec's UTC-aware datetime representation.
- Calendar-date logical defaults reject datetime values where a pure date is required.
- Logical type defaults for date, time, datetime, and UUID are emitted as Avro's underlying primitive JSON values.
- Decimal logical defaults are deferred.
- Supported logical types compose through nullable fields, arrays, and string-keyed maps.
- Pydantic `Field` attributes remain the canonical surface when they clearly translate to Avro: aliases for Avro Field Names, descriptions for Avro field docs, and supported defaults for Avro defaults.
- JSON Schema-only metadata is ignored for Avro Schema generation, even when it contains Avro-looking keys.
- Avro-specific metadata is supplied only through typed `Annotated[...]` helper objects.
- Pydantic `Field(...)` may appear inside or outside `Annotated[...]`; schema generation reads the normalized Pydantic field information and only parses Avro helper objects from annotation metadata.
- Unknown non-Avro `Annotated[...]` metadata is ignored.
- Duplicate, conflicting, or type-incompatible Avro helper metadata fails with Avro Schema generation errors.
- Record-level naming remains controlled by Avro model configuration; do not add competing `Annotated` record-name metadata in this slice.
- Public exports include the new decimal metadata helper alongside the existing Avro model base, config, and error types.
- Documentation should describe both inferred logical types and the explicit decimal metadata surface.

## Testing Decisions

- Use test-driven development with red-green-refactor cycles; write one public behavior test, implement the minimum code to pass it, then continue.
- Tests should exercise public model APIs for Avro Schema generation and Avro Message encode/decode rather than private parser internals.
- The tracer bullet should prove that an annotated Decimal field emits a bytes-backed Avro decimal logical schema that fastavro can parse.
- Test `AvroDecimal` constructor validation because it is public API behavior.
- Test bare Decimal schema generation failure with actionable guidance.
- Test decimal Avro Message round-trip through normal Pydantic validation.
- Test decimal metadata through named aliases and inside containers using public models.
- Test duplicate and type-incompatible decimal metadata failures through schema generation.
- Test date, time, datetime, and UUID schema mappings through generated raw Avro Schemas.
- Test logical type round-trips through Avro Message encode/decode.
- Test naive datetime encode failure and naive datetime default schema-generation failure.
- Test temporal and UUID defaults emit Avro primitive defaults.
- Existing schema tests for enums, aliases, defaults, nullable fields, containers, and named aliases are prior art for schema behavior.
- Existing codec tests for primitive, nested, alias, enum, literal, and validation-error round trips are prior art for Avro Message behavior.
- Avoid tests that assert the shape of internal parsed metadata objects unless that parser later becomes public API.

## Out of Scope

- Avro local timestamp logical types.
- Millisecond time or timestamp logical type selection knobs.
- Fixed-backed decimal logical types.
- Decimal Avro schema defaults.
- Avro helper objects for date, time, timestamp, UUID, docs, aliases, fixed, or integer width hints.
- Avro field alias metadata for reader/writer schema resolution.
- Record-level or enum-level naming through `Annotated[...]` metadata.
- Schema evolution with separate writer and reader schemas.
- Applying or validating `json_schema_extra` as Avro metadata.
- Pydantic constrained temporal types and subclass-based logical type inference.

## Further Notes

Two ADRs capture the core public API decisions: use Pydantic `Field` for clear Avro field metadata, and infer obvious Avro Logical Types from Python types. The implementation should keep those decisions visible in documentation and avoid introducing competing surfaces unless a later roadmap issue reopens the tradeoff explicitly.
