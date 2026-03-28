"""Data models for devices, overrides, and compatibility results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class VerdictType(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Panel:
    id: str
    manufacturer: str
    model: str
    frequencies: list[str]
    protocols: list[str]
    platform: str = ""
    notes: str = ""
    discontinued: bool = False

    @property
    def device_type(self) -> str:
        return "panel"

    @property
    def display_name(self) -> str:
        return f"{self.manufacturer} {self.model}"


@dataclass(frozen=True)
class Sensor:
    id: str
    manufacturer: str
    model: str
    sensor_type: str
    frequency: str
    protocol: str
    platform: str = ""
    notes: str = ""
    discontinued: bool = False

    @property
    def device_type(self) -> str:
        return "sensor"

    @property
    def display_name(self) -> str:
        return f"{self.manufacturer} {self.model}"


@dataclass(frozen=True)
class Peripheral:
    id: str
    manufacturer: str
    model: str
    peripheral_type: str
    protocols: list[str]
    platform: str = ""
    notes: str = ""
    discontinued: bool = False

    @property
    def device_type(self) -> str:
        return "peripheral"

    @property
    def display_name(self) -> str:
        return f"{self.manufacturer} {self.model}"


# Union type for any device
Device = Panel | Sensor | Peripheral


@dataclass(frozen=True)
class Override:
    device_a: str
    device_b: str
    verdict: str
    condition: str = ""
    limitations: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    source: str = ""

    def matches(self, id_a: str, id_b: str) -> bool:
        pair = {id_a, id_b}
        return pair == {self.device_a, self.device_b}


@dataclass
class CompatResult:
    verdict: VerdictType
    explanation: str
    requirements: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
