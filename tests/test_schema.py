from __future__ import annotations

from enum import Enum
from typing import Literal, cast

import pytest
from pydantic import Field

from pydantic_avro import AvroBaseModel, AvroSchemaGenerationError


type OpType = Literal["CREATE", "DELETE"]
type RenamedOpType = OpType
type Box[T] = list[T]
type UserId = int
type Tags = list[str]
ImportedOpType = OpType
PlainAssignmentOpType = Literal["CREATE", "DELETE"]


class OpenAlias:
    type Status = Literal["OPEN"]


class ClosedAlias:
    type Status = Literal["CLOSED"]


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


def test_named_literal_alias_field_schema_uses_alias_name() -> None:
    class Event(AvroBaseModel):
        op_type: OpType

    schema = Event.model_avro_schema()
    op_type = field(schema, "op_type")

    assert op_type["type"]["type"] == "enum"
    assert op_type["type"]["name"] == "OpType"
    assert op_type["type"]["namespace"] == schema["namespace"]
    assert op_type["type"]["symbols"] == ["CREATE", "DELETE"]


def test_reused_named_literal_alias_is_referenced() -> None:
    class Event(AvroBaseModel):
        first: OpType
        second: OpType

    schema = Event.model_avro_schema()
    first = field(schema, "first")
    second = field(schema, "second")

    assert first["type"]["type"] == "enum"
    assert second["type"] == f"{schema['namespace']}.OpType"


def test_nullable_named_literal_alias_uses_named_enum() -> None:
    class Event(AvroBaseModel):
        op_type: OpType | None = None

    op_type = field(Event.model_avro_schema(), "op_type")

    assert op_type["type"][0] == "null"
    assert op_type["type"][1]["type"] == "enum"
    assert op_type["type"][1]["name"] == "OpType"
    assert op_type["default"] is None


def test_named_literal_alias_is_supported_inside_containers() -> None:
    class Event(AvroBaseModel):
        ops: list[OpType]
        by_id: dict[str, OpType]

    schema = Event.model_avro_schema()
    ops = field(schema, "ops")
    by_id = field(schema, "by_id")

    assert ops["type"]["items"]["type"] == "enum"
    assert ops["type"]["items"]["name"] == "OpType"
    assert by_id["type"]["values"] == f"{schema['namespace']}.OpType"


def test_plain_assignment_literal_alias_stays_field_local() -> None:
    class Event(AvroBaseModel):
        op_type: PlainAssignmentOpType

    op_type = field(Event.model_avro_schema(), "op_type")

    assert op_type["type"]["name"] == "Event_op_type_Enum"


def test_plain_assignment_literal_alias_inside_container_gives_named_alias_guidance() -> None:
    class Bad(AvroBaseModel):
        ops: list[PlainAssignmentOpType]

    with pytest.raises(AvroSchemaGenerationError, match="named type alias"):
        Bad.model_avro_schema()


def test_outer_named_literal_alias_name_wins() -> None:
    class Event(AvroBaseModel):
        op_type: RenamedOpType

    op_type = field(Event.model_avro_schema(), "op_type")

    assert op_type["type"]["name"] == "RenamedOpType"


def test_import_alias_does_not_rename_named_literal_alias() -> None:
    class Event(AvroBaseModel):
        op_type: ImportedOpType

    op_type = field(Event.model_avro_schema(), "op_type")

    assert op_type["type"]["name"] == "OpType"


def test_named_literal_alias_name_collision_with_different_symbols_is_error() -> None:
    class Ticket(AvroBaseModel):
        open_status: OpenAlias.Status
        closed_status: ClosedAlias.Status

    with pytest.raises(AvroSchemaGenerationError, match="reuses Avro name"):
        Ticket.model_avro_schema()


def test_generic_type_alias_is_rejected() -> None:
    class Bad(AvroBaseModel):
        values: Box[int]

    with pytest.raises(AvroSchemaGenerationError, match="generic type alias"):
        Bad.model_avro_schema()


def test_non_literal_type_alias_unwraps_transparently() -> None:
    class User(AvroBaseModel):
        id: UserId
        tags: Tags

    schema = User.model_avro_schema()

    assert field(schema, "id")["type"] == "long"
    assert field(schema, "tags")["type"] == {"type": "array", "items": "string"}


def test_non_literal_type_alias_collection_default_unwraps_transparently() -> None:
    class User(AvroBaseModel):
        tags: Tags = ["admin"]

    tags = field(User.model_avro_schema(), "tags")

    assert tags["default"] == ["admin"]


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


def test_builtin_list_default_factory_emits_array_default() -> None:
    class Example(AvroBaseModel):
        values: list[int] = Field(default_factory=list)

    values = field(Example.model_avro_schema(), "values")

    assert values["type"] == {"type": "array", "items": "long"}
    assert values["default"] == []


def test_builtin_dict_default_factory_emits_map_default() -> None:
    class Example(AvroBaseModel):
        values: dict[str, int] = Field(default_factory=dict)

    values = field(Example.model_avro_schema(), "values")

    assert values["type"] == {"type": "map", "values": "long"}
    assert values["default"] == {}


def test_rejects_unsupported_default_factory() -> None:
    class Bad(AvroBaseModel):
        values: list[int] = Field(default_factory=lambda: [])

    with pytest.raises(AvroSchemaGenerationError, match="default_factory.*values"):
        Bad.model_avro_schema()


def test_rejects_non_string_map_key() -> None:
    class Bad(AvroBaseModel):
        values: dict[int, str]

    with pytest.raises(AvroSchemaGenerationError, match="non-string"):
        Bad.model_avro_schema()


def test_list_default_emits_array_default() -> None:
    class Example(AvroBaseModel):
        values: list[int] = [1, 2]

    values = field(Example.model_avro_schema(), "values")

    assert values["default"] == [1, 2]


def test_dict_default_emits_map_default() -> None:
    class Example(AvroBaseModel):
        values: dict[str, str] = {"x": "y"}

    values = field(Example.model_avro_schema(), "values")

    assert values["default"] == {"x": "y"}


def test_collection_defaults_convert_enum_and_nullable_values() -> None:
    class Color(str, Enum):
        RED = "RED"

    class Example(AvroBaseModel):
        colors: list[Color] = [Color.RED]
        values: dict[str, int | None] = {"x": None}

    schema = Example.model_avro_schema()

    assert field(schema, "colors")["default"] == ["RED"]
    assert field(schema, "values")["default"] == {"x": None}


def test_rejects_map_default_with_non_string_keys() -> None:
    class Bad(AvroBaseModel):
        values: dict[str, int] = cast(dict[str, int], {1: 2})

    with pytest.raises(AvroSchemaGenerationError, match="values.*non-string"):
        Bad.model_avro_schema()


def test_rejects_collection_default_with_wrong_runtime_type() -> None:
    class BadList(AvroBaseModel):
        values: list[int] = cast(list[int], "oops")

    class BadDict(AvroBaseModel):
        values: dict[str, int] = cast(dict[str, int], "oops")

    with pytest.raises(AvroSchemaGenerationError, match="values.*default"):
        BadList.model_avro_schema()
    with pytest.raises(AvroSchemaGenerationError, match="values.*default"):
        BadDict.model_avro_schema()


def test_nullable_list_default_factory_orders_array_first() -> None:
    class Example(AvroBaseModel):
        values: list[int] | None = Field(default_factory=list)

    values = field(Example.model_avro_schema(), "values")

    assert values["type"] == [{"type": "array", "items": "long"}, "null"]
    assert values["default"] == []


def test_rejects_nested_record_default() -> None:
    class Child(AvroBaseModel):
        id: int

    class Parent(AvroBaseModel):
        child: Child = Child(id=1)

    with pytest.raises(AvroSchemaGenerationError, match="child.*default"):
        Parent.model_avro_schema()


def test_empty_list_of_records_default_is_supported() -> None:
    class Child(AvroBaseModel):
        id: int

    class Parent(AvroBaseModel):
        children: list[Child] = Field(default_factory=list)

    children = field(Parent.model_avro_schema(), "children")

    assert children["type"]["type"] == "array"
    assert children["type"]["items"]["type"] == "record"
    assert children["default"] == []


def test_model_avro_schema_returns_fresh_dict() -> None:
    class User(AvroBaseModel):
        id: int

    first = User.model_avro_schema()
    first["fields"].clear()

    assert User.model_avro_schema()["fields"]
