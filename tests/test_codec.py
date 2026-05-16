from __future__ import annotations

from enum import Enum
from typing import Any, Literal

import pytest
from pydantic import Field, ValidationError, field_validator

from pydantic_avro import AvroBaseModel, AvroDecodeError


def test_round_trips_primitive_model() -> None:
    class User(AvroBaseModel):
        id: int
        name: str
        active: bool = True

    user = User(id=1, name="Ada")

    payload = user.model_dump_avro()

    assert isinstance(payload, bytes)
    assert User.model_validate_avro(payload) == user


def test_round_trips_nested_model() -> None:
    class Address(AvroBaseModel):
        street: str

    class User(AvroBaseModel):
        home: Address

    user = User(home=Address(street="1 Main"))

    assert User.model_validate_avro(user.model_dump_avro()) == user


def test_round_trips_alias_field() -> None:
    class User(AvroBaseModel):
        user_id: int = Field(alias="userId")

    user = User(userId=1)

    assert User.model_validate_avro(user.model_dump_avro()).user_id == 1


def test_round_trips_serialization_alias_field() -> None:
    class User(AvroBaseModel):
        user_id: int = Field(serialization_alias="userId")

    user = User(user_id=1)

    assert User.model_validate_avro(user.model_dump_avro()).user_id == 1


def test_round_trips_enum_values() -> None:
    class Color(str, Enum):
        RED = "RED"
        BLUE = "BLUE"

    class Paint(AvroBaseModel):
        color: Color

    paint = Paint(color=Color.BLUE)

    assert Paint.model_validate_avro(paint.model_dump_avro()) == paint


def test_round_trips_enum_names_for_non_string_values() -> None:
    class Color(Enum):
        RED = 1
        BLUE = 2

    class Paint(AvroBaseModel):
        color: Color
        palette: list[Color]

    paint = Paint(color=Color.BLUE, palette=[Color.RED])

    assert Paint.model_validate_avro(paint.model_dump_avro()) == paint


def test_round_trips_literal_enum_field() -> None:
    class Event(AvroBaseModel):
        kind: Literal["CREATED", "DELETED"]

    event = Event(kind="DELETED")

    assert Event.model_validate_avro(event.model_dump_avro()) == event


def test_invalid_bytes_raise_decode_error() -> None:
    class User(AvroBaseModel):
        id: int

    with pytest.raises(AvroDecodeError):
        User.model_validate_avro(b"")


def test_decode_type_error_is_decode_error() -> None:
    class User(AvroBaseModel):
        id: int

    bad_data: Any = "not bytes"
    with pytest.raises(AvroDecodeError):
        User.model_validate_avro(bad_data)


def test_pydantic_validation_error_is_not_wrapped() -> None:
    class User(AvroBaseModel):
        id: int

        @field_validator("id")
        @classmethod
        def reject_one(cls, value: int) -> int:
            if value == 1:
                raise ValueError("bad id")
            return value

    class WireUser(AvroBaseModel):
        id: int

    payload = WireUser(id=1).model_dump_avro()

    with pytest.raises(ValidationError):
        User.model_validate_avro(payload)
