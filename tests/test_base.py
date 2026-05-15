from __future__ import annotations

import json

from pydantic_avro import AvroBaseModel, AvroConfigDict


def test_schema_json_matches_schema() -> None:
    class User(AvroBaseModel):
        id: int

    assert json.loads(User.model_avro_schema_json()) == User.model_avro_schema()


def test_avro_config_overrides_name_and_namespace() -> None:
    class User(AvroBaseModel):
        model_config = AvroConfigDict(avro_name="Account", avro_namespace="com.example")
        id: int

    schema = User.model_avro_schema()

    assert schema["name"] == "Account"
    assert schema["namespace"] == "com.example"
