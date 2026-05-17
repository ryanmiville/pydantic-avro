# Use Pydantic Field for clear Avro field metadata

Status: Accepted

Avro-specific schema choices are supplied through typed `Annotated[...]` helper objects, but the library should not duplicate Pydantic `Field` attributes that already have clear Avro equivalents. Field aliases define Avro field names, field descriptions define Avro field `doc`, and supported defaults define Avro defaults; JSON Schema-only metadata such as `title` and `json_schema_extra` is ignored rather than treated as Avro metadata.
