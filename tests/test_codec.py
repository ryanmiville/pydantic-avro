from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Literal
from uuid import UUID

import pytest
from pydantic import Field, ValidationError, field_validator

from pydantic_avro import AvroBaseModel, AvroDecimal, AvroDecodeError, AvroEncodeError


type Money = Annotated[Decimal, AvroDecimal(precision=12, scale=2)]


def test_round_trips_annotated_decimal() -> None:
    class Invoice(AvroBaseModel):
        amount: Annotated[Decimal, AvroDecimal(precision=12, scale=2)]

    invoice = Invoice(amount=Decimal("123.45"))

    assert Invoice.model_validate_avro(invoice.model_dump_avro()) == invoice


def test_round_trips_named_decimal_alias_inside_containers() -> None:
    class InvoiceBatch(AvroBaseModel):
        amounts: list[Money]
        totals: dict[str, Money]

    batch = InvoiceBatch(
        amounts=[Decimal("123.45")],
        totals={"usd": Decimal("123.45")},
    )

    assert InvoiceBatch.model_validate_avro(batch.model_dump_avro()) == batch


def test_round_trips_date_time_and_uuid_logical_values() -> None:
    class Event(AvroBaseModel):
        starts_on: date
        starts_at: time
        event_id: UUID

    event = Event(
        starts_on=date(2024, 2, 29),
        starts_at=time(12, 34, 56, 789),
        event_id=UUID("12345678-1234-5678-1234-567812345678"),
    )

    assert Event.model_validate_avro(event.model_dump_avro()) == event


def test_round_trips_aware_datetime_as_utc_timestamp() -> None:
    class Event(AvroBaseModel):
        occurred_at: datetime

    event = Event(
        occurred_at=datetime.fromisoformat("2024-01-02T03:04:05.000006-05:00")
    )

    decoded = Event.model_validate_avro(event.model_dump_avro())

    assert decoded.occurred_at == datetime(2024, 1, 2, 8, 4, 5, 6, tzinfo=timezone.utc)


def test_naive_datetime_encode_fails_clearly() -> None:
    class Event(AvroBaseModel):
        occurred_at: datetime

    event = Event(occurred_at=datetime(2024, 1, 2, 3, 4, 5, 6))

    with pytest.raises(AvroEncodeError, match="timezone-aware"):
        event.model_dump_avro()


def test_round_trips_datetime_inside_nullable_array_and_map() -> None:
    class Event(AvroBaseModel):
        maybe_occurred_at: datetime | None = None
        reminders: list[datetime]
        by_id: dict[str, datetime]

    timestamp = datetime.fromisoformat("2024-01-02T03:04:05.000006-05:00")
    event = Event(
        maybe_occurred_at=timestamp,
        reminders=[timestamp],
        by_id={"a": timestamp},
    )

    decoded = Event.model_validate_avro(event.model_dump_avro())

    utc_timestamp = datetime(2024, 1, 2, 8, 4, 5, 6, tzinfo=timezone.utc)
    assert decoded == Event(
        maybe_occurred_at=utc_timestamp,
        reminders=[utc_timestamp],
        by_id={"a": utc_timestamp},
    )


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
