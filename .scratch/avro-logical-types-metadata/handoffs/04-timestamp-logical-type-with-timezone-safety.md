# Handoff: issue 04 timestamp logical type with timezone safety

## Focus

Implement `.scratch/avro-logical-types-metadata/issues/04-timestamp-logical-type-with-timezone-safety.md`.

Use TDD / red-green-refactor. Issue 04 depends on issue 01 being done; verify current code state before starting.

## Must-read artifacts

- Parent PRD: `.scratch/avro-logical-types-metadata/PRD.md`
- Target issue: `.scratch/avro-logical-types-metadata/issues/04-timestamp-logical-type-with-timezone-safety.md`
- Domain glossary: `CONTEXT.md`
- ADRs:
  - `docs/adr/0003-use-pydantic-field-for-clear-avro-field-metadata.md`
  - `docs/adr/0004-infer-obvious-avro-logical-types-from-python-types.md`
- TDD skill: `/Users/ryanmiville/.pi/agent/skills/tdd/SKILL.md`

## Relevant code entry points

- Schema generation: `src/pydantic_avro/schema.py`
- Avro/Pydantic value conversion: `src/pydantic_avro/conversion.py`
- Codec wrapping/cache: `src/pydantic_avro/codec.py`
- Public model API: `src/pydantic_avro/base.py`
- Existing schema tests: `tests/test_schema.py`
- Existing codec tests: `tests/test_codec.py`

## Conversation decisions not to reopen

Captured in PRD/CONTEXT/ADRs, but especially relevant for issue 04:

- Plain stdlib `datetime.datetime` annotation maps to Avro `long` + `logicalType: timestamp-micros`.
- Do not infer Avro local timestamp semantics from plain `datetime`.
- Encoding timestamp logical values requires timezone-aware datetimes.
- Fastavro accepts naive datetimes and interprets them using local timezone; this is exactly why pydantic-avro should reject them before codec write.
- Decode should preserve fastavro's UTC-aware `datetime` result; do not try to restore original timezone.
- Naive datetime defaults should fail schema generation, not depend on machine timezone.
- Timestamp defaults emit Avro primitive micros-since-epoch JSON values.
- Timestamp logical type should compose through nullable, list, and `dict[str, T]` paths.

## Suggested RGR sequence

1. RED: schema test for `datetime` field emits `timestamp-micros` and parses with fastavro.
2. GREEN: minimal schema mapping.
3. RED/GREEN: timezone-aware datetime round-trip through `model_dump_avro` / `model_validate_avro`.
4. RED/GREEN: naive datetime encode fails as `AvroEncodeError` with clear message.
5. RED/GREEN: naive datetime default fails as `AvroSchemaGenerationError`.
6. RED/GREEN: aware datetime default emits primitive microseconds since epoch.
7. RED/GREEN: nullable/list/map composition.
8. Refactor only after green; keep tests public-interface-focused.

## Watch-outs

- Python `datetime` subclasses `date`; avoid accidental date handling if issue 03 is already implemented.
- Existing conversion path currently returns values unchanged unless enum/model/container handling applies. Timestamp encode validation likely belongs near `to_avro_value`, with path-aware errors if practical.
- `encode_avro` wraps codec exceptions as `AvroEncodeError`; if validation happens before `encode_avro`, ensure user still sees an Avro encode failure for naive message values.
- Do not add `AvroTimestamp`, millis knobs, or local timestamp metadata in this issue.
- Do not write tests against private parser internals.

## Suggested skills next session

- `tdd` for implementation.
- `diagnose` only if fastavro/Pydantic behavior is surprising or a regression is hard to isolate.
