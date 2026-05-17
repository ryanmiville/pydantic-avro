from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class AvroDecimal:
    """Avro decimal logical type metadata for Decimal annotations."""

    precision: int
    scale: int

    def __post_init__(self) -> None:
        if not isinstance(self.precision, int) or isinstance(self.precision, bool):
            raise ValueError("AvroDecimal precision must be an integer")
        if not isinstance(self.scale, int) or isinstance(self.scale, bool):
            raise ValueError("AvroDecimal scale must be an integer")
        if self.precision <= 0:
            raise ValueError("AvroDecimal precision must be greater than 0")
        if self.scale < 0:
            raise ValueError("AvroDecimal scale must be greater than or equal to 0")
        if self.scale > self.precision:
            raise ValueError("AvroDecimal scale must be less than or equal to precision")
