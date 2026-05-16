from __future__ import annotations

from enum import Enum
from typing import Literal

import pytest
from pydantic import Field

from pydantic_avro import AvroBaseModel, AvroSchemaGenerationError


def field(schema: dict, name: str) -> dict:
    return next(item for item in schema["fields"] if item["name"] == name)


def test_primitive_record_schema() -> None:
    class User(AvroBaseModel):
        id: int
        name: str
        active: bool

    schema = User.model_avro_schema()

    assert schema["type"] == "record"
    assert schema["name"] == "User"
    assert [(item["name"], item["type"]) for item in schema["fields"]] == [
        ("id", "long"),
        ("name", "string"),
        ("active", "boolean"),
    ]


def test_optional_default_none_orders_null_first() -> None:
    class User(AvroBaseModel):
        email: str | None = None

    email = field(User.model_avro_schema(), "email")

    assert email["type"] == ["null", "string"]
    assert email["default"] is None


def test_optional_non_null_default_orders_value_first() -> None:
    class User(AvroBaseModel):
        nickname: str | None = "anon"

    nickname = field(User.model_avro_schema(), "nickname")

    assert nickname["type"] == ["string", "null"]
    assert nickname["default"] == "anon"


def test_alias_and_docs() -> None:
    class User(AvroBaseModel):
        """A user account."""

        user_id: int = Field(serialization_alias="userId", description="External id")

    schema = User.model_avro_schema()

    assert schema["doc"] == "A user account."
    assert field(schema, "userId") == {
        "name": "userId",
        "type": "long",
        "doc": "External id",
    }


def test_nested_model_is_referenced_when_repeated() -> None:
    class Address(AvroBaseModel):
        street: str

    class User(AvroBaseModel):
        home: Address
        work: Address

    schema = User.model_avro_schema()
    home_type = field(schema, "home")["type"]
    work_type = field(schema, "work")["type"]

    assert home_type["type"] == "record"
    assert home_type["name"] == "Address"
    assert work_type == f"{home_type['namespace']}.Address"


def test_enum_schema_and_default() -> None:
    class Color(str, Enum):
        RED = "RED"
        BLUE = "BLUE"

    class Paint(AvroBaseModel):
        color: Color = Color.RED

    color = field(Paint.model_avro_schema(), "color")

    assert color["type"]["type"] == "enum"
    assert color["type"]["symbols"] == ["RED", "BLUE"]
    assert color["default"] == "RED"


def test_string_literal_field_schema_is_enum() -> None:
    class Event(AvroBaseModel):
        kind: Literal["CREATED", "DELETED"]

    kind = field(Event.model_avro_schema(), "kind")

    assert kind["type"]["type"] == "enum"
    assert kind["type"]["name"] == "Event_kind_Enum"
    assert kind["type"]["symbols"] == ["CREATED", "DELETED"]


def test_single_value_literal_schema_is_one_symbol_enum() -> None:
    class Event(AvroBaseModel):
        event_type: Literal["neo_delta"]

    event_type = field(Event.model_avro_schema(), "event_type")

    assert event_type["type"]["type"] == "enum"
    assert event_type["type"]["symbols"] == ["neo_delta"]


def test_nullable_literal_schema_orders_null_first_with_none_default() -> None:
    class Ticket(AvroBaseModel):
        status: Literal["OPEN", "CLOSED"] | None = None

    status = field(Ticket.model_avro_schema(), "status")

    assert status["type"][0] == "null"
    assert status["type"][1]["type"] == "enum"
    assert status["type"][1]["name"] == "Ticket_status_Enum"
    assert status["type"][1]["symbols"] == ["OPEN", "CLOSED"]
    assert status["default"] is None


def test_rejects_non_string_literal() -> None:
    class Bad(AvroBaseModel):
        value: Literal[1, 2]

    with pytest.raises(AvroSchemaGenerationError, match="value"):
        Bad.model_avro_schema()


def test_rejects_invalid_literal_symbol() -> None:
    class Bad(AvroBaseModel):
        value: Literal["bad-symbol"]

    with pytest.raises(AvroSchemaGenerationError, match="value"):
        Bad.model_avro_schema()


def test_rejects_literal_inside_list() -> None:
    class Bad(AvroBaseModel):
        values: list[Literal["A", "B"]]

    with pytest.raises(AvroSchemaGenerationError, match="values"):
        Bad.model_avro_schema()


def test_rejects_literal_inside_map() -> None:
    class Bad(AvroBaseModel):
        values: dict[str, Literal["A", "B"]]

    with pytest.raises(AvroSchemaGenerationError, match="values"):
        Bad.model_avro_schema()


def test_rejects_unsupported_union() -> None:
    class Bad(AvroBaseModel):
        value: int | str

    with pytest.raises(AvroSchemaGenerationError, match="value"):
        Bad.model_avro_schema()


def test_rejects_default_factory() -> None:
    class Bad(AvroBaseModel):
        values: list[int] = Field(default_factory=list)

    with pytest.raises(AvroSchemaGenerationError, match="default_factory"):
        Bad.model_avro_schema()


def test_rejects_non_string_map_key() -> None:
    class Bad(AvroBaseModel):
        values: dict[int, str]

    with pytest.raises(AvroSchemaGenerationError, match="non-string"):
        Bad.model_avro_schema()


def test_rejects_complex_default() -> None:
    class Bad(AvroBaseModel):
        values: list[int] = []

    with pytest.raises(AvroSchemaGenerationError, match="default"):
        Bad.model_avro_schema()


def test_model_avro_schema_returns_fresh_dict() -> None:
    class User(AvroBaseModel):
        id: int

    first = User.model_avro_schema()
    first["fields"].clear()

    assert User.model_avro_schema()["fields"]
