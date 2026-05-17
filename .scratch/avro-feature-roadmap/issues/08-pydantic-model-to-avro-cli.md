# Pydantic model to Avro schema CLI

Status: needs-triage

## What to build

Add a CLI command that imports a Pydantic Avro model by dotted path and writes its generated raw Avro schema as JSON.

## Acceptance criteria

- [ ] CLI accepts a dotted model path and output path.
- [ ] Generated output matches `model_avro_schema()` semantics.
- [ ] Import, schema-generation, and file-write errors are reported clearly.
- [ ] Command can emit compact or pretty JSON.
- [ ] Tests cover successful generation and common failure modes.

## Blocked by

- `.scratch/avro-feature-roadmap/issues/06-recursive-models.md`
