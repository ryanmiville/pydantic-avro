# Logical types

Status: needs-triage

## What to build

Add first-class Avro logical type support for Pydantic/Python types, preserving round-trip encode/decode behavior through Avro messages and generating valid raw Avro schemas.

## Acceptance criteria

- [ ] `date`, `time`, `datetime`, `Decimal`, and `UUID` mappings are documented and tested.
- [ ] Generated schemas include the correct Avro `logicalType` metadata and remain `fastavro`-parseable.
- [ ] Avro message encode/decode round trips through Pydantic validation for supported logical types.
- [ ] Unsupported or under-specified logical type cases fail with `AvroSchemaGenerationError`.

## Resolved design

- Infer logical types from exact standard-library annotations when there is one obvious mapping:
  - `datetime.date` -> Avro `int` + `logicalType: date`
  - `datetime.time` -> Avro `long` + `logicalType: time-micros`
  - `datetime.datetime` -> Avro `long` + `logicalType: timestamp-micros`
  - `uuid.UUID` -> Avro `string` + `logicalType: uuid`
- `datetime.datetime` values and defaults must be timezone-aware; Avro stores a UTC instant and does not preserve original timezone identity.
- Decoding `timestamp-micros` preserves fastavro's UTC-aware `datetime` result.
- `decimal.Decimal` requires explicit `Annotated[Decimal, AvroDecimal(precision=..., scale=...)]`; bare `Decimal` is under-specified and errors.
- First decimal support is bytes-backed decimal; fixed-backed decimal is deferred.
- `AvroDecimal` is a frozen keyword-only helper that validates `precision > 0`, `scale >= 0`, and `scale <= precision` at construction time with normal Python value errors.
- Logical defaults are emitted as Avro's underlying primitive JSON values for date/time/datetime/UUID; decimal defaults are deferred.
- Calendar-date logical values reject `datetime` values where a pure `date` is required.
- Supported logical types compose through nullable fields, arrays, and string-keyed maps.
- Decimal value precision/scale validity is left to the Avro codec during message encoding and wrapped as `AvroEncodeError` if it fails.

## Blocked by

None - can start immediately
