# Handoff: implement issue 02 — Decimal metadata composition and conflicts

## Next focus

Implement `.scratch/avro-logical-types-metadata/issues/02-decimal-metadata-composition-and-conflicts.md` after issue 01 is complete. This is a TDD/RGR vertical slice: extend the already-working `AvroDecimal` tracer so Avro Metadata composes through aliases/containers and rejects conflicts.

## Use these skills

- `tdd` — required; use one RED → GREEN behavior at a time.
- `diagnose` — only if fastavro/Pydantic alias/Annotated behavior gets surprising.
- `grill-with-docs` — not needed unless reopening design decisions.

## Canonical artifacts

Read these, do not rediscover design from chat:

- Parent PRD: `.scratch/avro-logical-types-metadata/PRD.md`
- Target issue: `.scratch/avro-logical-types-metadata/issues/02-decimal-metadata-composition-and-conflicts.md`
- Blocker issue: `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
- Domain glossary: `CONTEXT.md`
- ADRs:
  - `docs/adr/0003-use-pydantic-field-for-clear-avro-field-metadata.md`
  - `docs/adr/0004-infer-obvious-avro-logical-types-from-python-types.md`

## Current design constraints relevant to issue 02

- Avro-specific metadata lives only in typed `Annotated[...]` helper objects.
- Unknown non-Avro `Annotated[...]` metadata is ignored.
- Pydantic `Field(...)` can appear inside or outside `Annotated[...]`; use normalized `model_fields` for Field-derived Avro behavior.
- Metadata attached to a named alias must apply everywhere the alias is used, including nullable fields, arrays, and string-keyed maps.
- Duplicate/conflicting/type-incompatible Avro Metadata fails with `AvroSchemaGenerationError`.
- Tests should verify public behavior via `model_avro_schema()` and Avro Message round-trips, not private parser object shape.

## Likely implementation shape

Assuming issue 01 introduced `AvroDecimal` and basic metadata parsing, deepen that parser rather than scattering `Annotated` handling through schema/conversion/default code. The goal is a small stable interface: parse an annotation into base annotation + recognized Avro Metadata, preserving metadata through `TypeAliasType`, nullable, list, and dict recursion.

Watch current pre-issue code patterns:

- `schema.py` currently has `unwrap_annotated()` and `parse_type_alias()` paths that may discard metadata.
- `conversion.py` also unwraps annotations; issue 02 may need matching metadata-aware recursion for Decimal values inside aliases/containers.
- Existing named Literal alias behavior in tests is useful prior art for alias reuse/collision expectations.

## Suggested RGR order

1. Named alias carries `AvroDecimal` metadata at direct field use.
2. Alias works in nullable field.
3. Alias/Annotated Decimal works inside `list[...]`.
4. Alias/Annotated Decimal works inside `dict[str, ...]`.
5. Unknown non-Avro `Annotated` marker is ignored.
6. Duplicate/conflicting decimal metadata errors.
7. `AvroDecimal` on non-Decimal base annotation errors.
8. Add/adjust round-trip tests where schema-only tests are insufficient.

Keep each cycle minimal. Do not implement date/time/UUID/timestamp behavior here; those are later issues.

## Worktree note

At handoff creation, design artifacts are modified/untracked (`CONTEXT.md`, `.scratch/`, ADR 0003/0004). Do not assume a clean tree.
