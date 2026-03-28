"""Device database — load JSON files, search, filter, export."""

from __future__ import annotations

import json
import os
from pathlib import Path

from rapidfuzz import fuzz, process

from .models import Device, Override, Panel, Peripheral, Sensor


def _default_data_dir() -> Path:
    """Resolve data directory: env var > package-relative > cwd."""
    env = os.environ.get("BASTION_DATA_DIR")
    if env:
        return Path(env)
    pkg_relative = Path(__file__).resolve().parent.parent.parent / "data"
    if pkg_relative.is_dir():
        return pkg_relative
    return Path("data")


class DeviceDB:
    def __init__(self, data_dir: Path | None = None):
        self._data_dir = data_dir or _default_data_dir()
        self._devices: dict[str, Device] = {}
        self.overrides: list[Override] = []
        self._load()

    def _load(self):
        self._load_panels()
        self._load_sensors()
        self._load_peripherals()
        self._load_overrides()

    def _load_panels(self):
        path = self._data_dir / "panels.json"
        for raw in json.loads(path.read_text(encoding="utf-8")):
            panel = Panel(
                id=raw["id"],
                manufacturer=raw["manufacturer"],
                model=raw["model"],
                frequencies=raw.get("frequencies", []),
                protocols=raw.get("protocols", []),
                platform=raw.get("platform", ""),
                notes=raw.get("notes", ""),
                discontinued=raw.get("discontinued", False),
            )
            self._devices[panel.id] = panel

    def _load_sensors(self):
        path = self._data_dir / "sensors.json"
        for raw in json.loads(path.read_text(encoding="utf-8")):
            sensor = Sensor(
                id=raw["id"],
                manufacturer=raw["manufacturer"],
                model=raw["model"],
                sensor_type=raw.get("sensor_type", raw.get("type", "")),
                frequency=raw.get("frequency", ""),
                protocol=raw.get("protocol", ""),
                platform=raw.get("platform", ""),
                notes=raw.get("notes", ""),
                discontinued=raw.get("discontinued", False),
            )
            self._devices[sensor.id] = sensor

    def _load_peripherals(self):
        path = self._data_dir / "peripherals.json"
        for raw in json.loads(path.read_text(encoding="utf-8")):
            peripheral = Peripheral(
                id=raw["id"],
                manufacturer=raw["manufacturer"],
                model=raw["model"],
                peripheral_type=raw.get("peripheral_type", raw.get("type", "")),
                protocols=raw.get("protocols", []),
                platform=raw.get("platform", ""),
                notes=raw.get("notes", ""),
                discontinued=raw.get("discontinued", False),
            )
            self._devices[peripheral.id] = peripheral

    def _load_overrides(self):
        path = self._data_dir / "overrides.json"
        for raw in json.loads(path.read_text(encoding="utf-8")):
            self.overrides.append(Override(
                device_a=raw["device_a"],
                device_b=raw["device_b"],
                verdict=raw["verdict"],
                condition=raw.get("condition", ""),
                limitations=raw.get("limitations", []),
                alternatives=raw.get("alternatives", []),
                source=raw.get("source", ""),
            ))

    def get(self, device_id: str) -> Device | None:
        return self._devices.get(device_id)

    def all_devices(self) -> list[Device]:
        return list(self._devices.values())

    def search(self, query: str, limit: int = 10) -> list[Device]:
        if not query.strip():
            return []
        choices = {d.id: d.display_name for d in self._devices.values()}
        results = process.extract(
            query, choices, scorer=fuzz.WRatio, limit=limit, score_cutoff=50,
        )
        return [self._devices[r[2]] for r in results]

    def filter(
        self,
        device_type: str | None = None,
        manufacturer: str | None = None,
        active_only: bool = False,
    ) -> list[Device]:
        devices = list(self._devices.values())
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        if manufacturer:
            devices = [d for d in devices if d.manufacturer == manufacturer]
        if active_only:
            devices = [d for d in devices if not d.discontinued]
        return devices

    def find_override(self, id_a: str, id_b: str) -> Override | None:
        for override in self.overrides:
            if override.matches(id_a, id_b):
                return override
        return None

    def export_all(self) -> list[dict]:
        result = []
        for d in self._devices.values():
            entry = {
                "id": d.id,
                "manufacturer": d.manufacturer,
                "model": d.model,
                "device_type": d.device_type,
                "display_name": d.display_name,
                "notes": d.notes,
                "discontinued": d.discontinued,
            }
            if isinstance(d, Panel):
                entry["frequencies"] = d.frequencies
                entry["protocols"] = d.protocols
                entry["platform"] = d.platform
            elif isinstance(d, Sensor):
                entry["sensor_type"] = d.sensor_type
                entry["frequency"] = d.frequency
                entry["protocol"] = d.protocol
            elif isinstance(d, Peripheral):
                entry["peripheral_type"] = d.peripheral_type
                entry["protocols"] = d.protocols
            result.append(entry)
        return result
