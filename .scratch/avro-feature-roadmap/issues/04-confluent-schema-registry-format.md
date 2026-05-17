# Confluent schema registry format

Status: needs-triage

## What to build

Add optional support for Confluent/schema-registry wire format while keeping the current schemaless Avro message API clean and unchanged.

## Acceptance criteria

- [ ] Encoding can prefix Avro payloads with Confluent magic byte and schema ID.
- [ ] Decoding can read the schema ID and validate/decode with a supplied schema lookup boundary.
- [ ] Schema registry client concerns are isolated behind a small adapter/protocol.
- [ ] Existing `model_dump_avro()` and `model_validate_avro()` behavior is unchanged.
- [ ] Docs clearly distinguish Avro messages, schema-registry messages, and object container files.

## Blocked by

None.
