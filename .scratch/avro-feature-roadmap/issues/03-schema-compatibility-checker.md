# Schema compatibility checker

Status: needs-triage

## What to build

Add an API that checks whether one Avro schema is compatible with another using Avro reader/writer schema-resolution semantics, supporting backward, forward, and full compatibility modes.

## Acceptance criteria

- [ ] API accepts raw Avro schema dictionaries and/or JSON strings.
- [ ] Backward compatibility means the new reader schema can read data written with the old writer schema.
- [ ] Forward compatibility means the old reader schema can read data written with the new writer schema.
- [ ] Result is structured, with `compatible`, errors, and warnings/notes.
- [ ] Tests cover added fields with defaults, removed fields, renamed fields with aliases, enum changes, type promotions, and incompatible type changes.

## Blocked by

- `.scratch/avro-feature-roadmap/issues/02-annotated-avro-metadata.md`
