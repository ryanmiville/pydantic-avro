from __future__ import annotations

from pydantic import Field

from pydantic_avro import AvroBaseModel, AvroConfigDict


class User(AvroBaseModel):
    """A user account."""

    model_config = AvroConfigDict(avro_namespace="com.example")

    id: int = Field(serialization_alias="userId")
    name: str
    email: str | None = Field(default=None, description="Contact email")


def smoke() -> None:
    user = User(id=1, name="Ada")

    schema = User.model_avro_schema()
    payload = user.model_dump_avro()
    decoded = User.model_validate_avro(payload)

    assert schema["name"] == "User"
    assert schema["namespace"] == "com.example"
    assert isinstance(payload, bytes)
    assert decoded == user


if __name__ == "__main__":
    smoke()
    print("pydantic-avro example smoke passed")
