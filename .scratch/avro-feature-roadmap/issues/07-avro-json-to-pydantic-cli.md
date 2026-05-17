# Avro schema JSON to Pydantic CLI

Status: needs-triage

## What to build

Add a CLI command that reads an Avro schema JSON file and generates Pydantic model source code that can be reviewed and committed.

## Acceptance criteria

- [ ] CLI accepts `.avsc`/JSON input and writes Python output.
- [ ] Records become Pydantic models, enums become Python enums or Literals, and logical types map to supported Python types.
- [ ] Generated code imports `AvroBaseModel` where appropriate.
- [ ] Unsupported Avro features are reported clearly instead of generating unsafe code.
- [ ] Tests cover nested records, enums, arrays, maps, nullable fields, and logical types.

## Blocked by

- `.scratch/avro-feature-roadmap/issues/06-recursive-models.md`
