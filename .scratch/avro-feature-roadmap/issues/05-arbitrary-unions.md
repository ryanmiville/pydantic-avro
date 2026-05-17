# Arbitrary unions

Status: needs-triage

## What to build

Extend union support beyond nullable `T | None` while preserving unambiguous Avro schemas and predictable Pydantic encode/decode behavior.

## Acceptance criteria

- [ ] Primitive unions such as `int | str` generate valid Avro unions and round trip.
- [ ] Record unions such as `Cat | Dog` generate named record branches and round trip.
- [ ] Ambiguous unions are rejected with clear errors rather than relying on surprising validation order.
- [ ] Nullable-union ordering and default behavior remains backward compatible.
- [ ] Docs explain how Avro branch selection maps to Pydantic union validation.

## Blocked by

- `.scratch/avro-feature-roadmap/issues/02-annotated-avro-metadata.md`
