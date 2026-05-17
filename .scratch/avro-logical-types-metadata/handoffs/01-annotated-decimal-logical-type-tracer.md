# Handoff: Issue 01 annotated Decimal logical type tracer

## Next focus

Implement `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md` using TDD / red-green-refactor.

## Start here

Read these artifacts first; they contain the decisions, so do not re-litigate unless implementation exposes a contradiction:

- Parent PRD: `.scratch/avro-logical-types-metadata/PRD.md`
- Target issue: `.scratch/avro-logical-types-metadata/issues/01-annotated-decimal-logical-type-tracer.md`
- Domain glossary: `CONTEXT.md`
- ADRs:
  - `docs/adr/0003-use-pydantic-field-for-clear-avro-field-metadata.md`
  - `docs/adr/0004-infer-obvious-avro-logical-types-from-python-types.md`

## Useful current code

- `src/pydantic_avro/schema.py` owns schema generation, type alias handling, `Annotated` unwrapping, defaults, and fastavro parse validation.
- `src/pydantic_avro/conversion.py` owns Python/Pydantic value conversion before encode and after decode.
- `src/pydantic_avro/codec.py` wraps fastavro encode/decode errors.
- `src/pydantic_avro/__init__.py` exports public API.
- `tests/test_schema.py` and `tests/test_codec.py` are the main prior art for public behavior tests.

## Implementation guidance

Use vertical TDD. First tracer should be a public behavior test proving:

- `Annotated[Decimal, AvroDecimal(precision=12, scale=2)]` emits bytes-backed Avro decimal schema.
- Generated schema remains fastavro-parseable.
- Decimal value round-trips through `model_dump_avro()` / `model_validate_avro()`.

Then add one behavior at a time from the issue acceptance criteria.

Likely minimal shape:

- Add a small public metadata helper module with frozen keyword-only `AvroDecimal`.
- Validate helper values in `__post_init__` with normal `ValueError`.
- Export `AvroDecimal` from package root.
- Replace schema generation's blind `unwrap_annotated()` path enough to preserve recognized Avro metadata for Decimal.
- Bare `Decimal` should raise `AvroSchemaGenerationError` with guidance to use `Annotated[Decimal, AvroDecimal(...)]`.
- Decimal defaults are unsupported in issue 01; reject clearly.

Avoid solving issue 02 early. Metadata through aliases/containers/conflicts beyond the issue 01 tracer can wait unless needed to keep the design clean.

## Suggested skills

- `tdd` — use for RGR loop.
- `diagnose` — only if fastavro Decimal behavior or Pydantic annotation resolution behaves unexpectedly.

## Verification

Run targeted tests first, then full suite:

- `uv run pytest tests/test_schema.py tests/test_codec.py`
- `uv run pytest`
- If available/fast enough: `uv run ruff check .` and `uv run ty check .`
