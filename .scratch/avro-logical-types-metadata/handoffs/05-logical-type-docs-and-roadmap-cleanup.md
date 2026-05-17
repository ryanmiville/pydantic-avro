# Handoff: issue 05 logical type docs and roadmap cleanup

## Focus

Implement `.scratch/avro-logical-types-metadata/issues/05-logical-type-docs-and-roadmap-cleanup.md` after its blockers are complete.

## Start here

- Parent PRD: `.scratch/avro-logical-types-metadata/PRD.md`
- Target issue: `.scratch/avro-logical-types-metadata/issues/05-logical-type-docs-and-roadmap-cleanup.md`
- Blockers:
  - `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
  - `.scratch/avro-logical-types-metadata/issues/02-decimal-metadata-composition-and-conflicts.md`
  - `.scratch/avro-logical-types-metadata/issues/03-date-time-and-uuid-logical-types.md`
  - `.scratch/avro-logical-types-metadata/issues/04-timestamp-logical-type-with-timezone-safety.md`
- Domain glossary: `CONTEXT.md`
- ADRs:
  - `docs/adr/0003-use-pydantic-field-for-clear-avro-field-metadata.md`
  - `docs/adr/0004-infer-obvious-avro-logical-types-from-python-types.md`

## Current state notes

This handoff was written immediately after design/grill + PRD/issue creation, before implementation of issues 01-04. Before doing issue 05, verify those blockers are actually implemented and tests pass. Do not assume README examples until code confirms public API and behavior.

Current uncommitted artifacts from this design session include `CONTEXT.md`, the two ADRs above, and `.scratch/avro-logical-types-metadata/**`.

## What issue 05 should do

Update user-facing docs and roadmap state to match implemented behavior. Likely docs target is `README.md`; only update other docs/examples if implementation made them relevant.

Must cover the acceptance criteria in issue 05, especially:

- inferred Avro Logical Type mapping table
- `Annotated[Decimal, AvroDecimal(precision=..., scale=...)]`
- bare `Decimal` rejected as under-specified
- timezone-aware datetime encode/default requirement + UTC-aware decode
- Pydantic `Field` reuse: aliases, descriptions, supported defaults
- JSON Schema-only metadata ignored: `title`, `examples`, `json_schema_extra`
- deferred features list
- roadmap issue status/details consistency

Use glossary terms exactly: **Avro Schema**, **Avro Message**, **Avro Logical Type**, **Avro Metadata**, **Avro Field Name**.

## Suggested skills

- Use `tdd` only if docs updates require doc/example tests or examples fail.
- Use `diagnose` if docs examples reveal mismatch between implemented behavior and accepted design.
- No need for `grill-with-docs`; design is already captured in PRD/ADRs/CONTEXT.

## Verification

Run the normal project checks after docs edits, at minimum:

- `uv run pytest`
- `uv run ruff check .`
- `uv run ty check .`

If implementation changed command names, follow `Makefile` / CI.
