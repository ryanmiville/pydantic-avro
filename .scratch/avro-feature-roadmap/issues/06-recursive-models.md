# Recursive models

Status: needs-triage

## What to build

Support recursive and mutually-recursive `AvroBaseModel` schemas by emitting named records once and referring to them by full Avro name when recursion is encountered.

## Acceptance criteria

- [ ] Direct self-recursive models generate valid Avro schemas.
- [ ] Mutually-recursive models generate valid Avro schemas.
- [ ] Encode/decode round trips recursive data through Avro messages and Pydantic validation.
- [ ] Unsupported recursion patterns fail with clear schema-generation errors.
- [ ] Existing repeated nested-record reference behavior remains unchanged.

## Blocked by

- `.scratch/avro-feature-roadmap/issues/05-arbitrary-unions.md`
