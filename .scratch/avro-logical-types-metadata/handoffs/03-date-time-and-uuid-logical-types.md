# Handoff: issue 03 date, time, and UUID logical types

## Focus

Implement `.scratch/avro-logical-types-metadata/issues/03-date-time-and-uuid-logical-types.md`.

Use **TDD / red-green-refactor**. One public behavior test at a time. Do not write a horizontal batch of tests.

## Required context

Read these first:

- `.scratch/avro-logical-types-metadata/issues/03-date-time-and-uuid-logical-types.md`
- `.scratch/avro-logical-types-metadata/PRD.md`
- `CONTEXT.md`
- `docs/adr/0003-use-pydantic-field-for-clear-avro-field-metadata.md`
- `docs/adr/0004-infer-obvious-avro-logical-types-from-python-types.md`

Issue 03 is blocked by issue 01. Before starting, verify `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md` is complete or that its implementation is already present.

## Current repo shape

Likely modules to touch:

- schema generation: `src/pydantic_avro/schema.py`
- value conversion: `src/pydantic_avro/conversion.py`
- codec wrapper only if needed: `src/pydantic_avro/codec.py`
- public docs/tests: `README.md`, `tests/test_schema.py`, `tests/test_codec.py`

Prior art:

- schema tests already assert raw Avro Schema through `model_avro_schema()`.
- codec tests already assert Avro Message round trips through `model_dump_avro()` / `model_validate_avro()`.

## Design reminders for issue 03

Implement only exact stdlib annotations for:

- `datetime.date` -> Avro `int` + `logicalType: date`
- `datetime.time` -> Avro `long` + `logicalType: time-micros`
- `uuid.UUID` -> Avro `string` + `logicalType: uuid`

Do not implement `datetime.datetime`; that is issue 04.

Do not infer UUID semantics from `str`.

Logical defaults should use Avro primitive JSON values:

- date: days since Unix epoch
- time-micros: microseconds since midnight
- uuid: string

Calendar-date defaults must reject `datetime.datetime` values where a pure `datetime.date` is required.

These logical types should compose through nullable fields, arrays, and string-keyed maps.

## Suggested RGR order

1. RED/GREEN: `date` field emits Avro date schema and parses with fastavro.
2. RED/GREEN: `time` field emits `time-micros` schema.
3. RED/GREEN: `UUID` field emits UUID schema; `str` unchanged.
4. RED/GREEN: round-trip date/time/UUID through Avro Message.
5. RED/GREEN: nullable/list/map composition for one or all three logical types.
6. RED/GREEN: defaults emit primitive values.
7. RED/GREEN: date default rejects `datetime` value.
8. Refactor shared logical-type/default helpers if duplication appears.

## Useful facts

A quick fastavro smoke test in the grill showed fastavro round-trips:

- date as `datetime.date`
- time-micros as `datetime.time`
- uuid as `uuid.UUID`

So prefer relying on fastavro for normal logical conversion rather than reimplementing encode/decode for these three, except for schema default encoding and the date-vs-datetime default guard.

## Skills for next session

- `tdd` — primary skill; implement via RGR.
- `diagnose` — only if fastavro/Pydantic behavior contradicts expectations.
