from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any

__all__ = (
    "SLIntEnum",
    "SLValueRange",
    "UnknownValue",
    "BODY_TYPE",
    "State",
    "NumericState",
    "ClampedNumericState",
    "EnumState",
    "BaseDevice",
)


class SLIntEnum(IntEnum):

    @property
    def title(self) -> str:
        return self._title()

    @classmethod
    def parse(cls, value: str, default=0) -> "SLIntEnum":
        """Attempt to return and Enum from the provided string."""
        try:
            return (
                cls(value)
                if isinstance(value, int)
                else (
                    cls(int(value))
                    if value.isdigit()
                    else cls[value.replace(" ", "_").replace("'", "").upper()]
                )
            )
        except (KeyError, ValueError):
            return None if default is None else cls(default)

    @classmethod
    def parsable_values(cls) -> tuple:
        """Return a tuple of all parsable values."""
        out = []
        for member in cls:
            out.extend([str(member.value), member.name.lower()])
        return tuple(out)

    def _title(self) -> str:
        return self.name.replace("_", " ").title()


@dataclass(frozen=True)
class SLValueRange:
    minimum: int | float
    maximum: int | float
    unit: str | None = None

    def check(self, value: int | float) -> None:
        if not self.in_range(value):
            raise ValueError(f"{value} not in range {self.minimum}-{self.maximum}")

    def in_range(self, value: int | float) -> bool:
        return self.minimum <= value <= self.maximum

    def parse_check(self, string: str) -> int | float:
        value = float(string) if isinstance(self.minimum, float) else int(string)
        if self.minimum <= value <= self.maximum:
            return value
        else:
            raise ValueError(f"{value} not in range {self.minimum}-{self.maximum}")


@dataclass
class UnknownValue:
    """Strucutre for data pertaining to unknown values in a ScreenLogic message."""

    value: int
    format: str


class BODY_TYPE(SLIntEnum):
    POOL = 0
    SPA = 1


class FrozenField:
    def __init__(self, value):
        self._value = value

    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, value):
        raise AttributeError("Cannot modify frozen field")


@dataclass
class State:
    name: str
    value: bool | Enum | float | int | str | None = None


@dataclass
class NumericState(State):
    unit: str | None = None


@dataclass
class ClampedNumericState(NumericState):
    range: SLValueRange = None


@dataclass
class EnumState(State):
    enum: Enum | None = None


@dataclass
class BaseDevice:
    """Base representation of a pool device controlled via ScreenLogic."""

    unknown_values: dict[int, dict[int, UnknownValue]] = field(default_factory=dict)
