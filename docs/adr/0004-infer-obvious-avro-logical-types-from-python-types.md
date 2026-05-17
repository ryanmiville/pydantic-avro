# Infer obvious Avro logical types from Python types

Status: Accepted

Plain Python value types should produce Avro logical types when there is one obvious, lossless mapping: `date` maps to `date`, `time` maps to `time-micros`, `datetime` maps to `timestamp-micros`, and `UUID` maps to `uuid`. `Decimal` is not inferred from the bare type because Avro requires precision and scale, so decimal fields must use explicit typed `Annotated[...]` metadata; bytes-backed decimal is supported first and fixed-backed decimal is deferred.
