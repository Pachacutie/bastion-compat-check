"""Tests for device database loading, search, and filtering."""

from bastion_compat.database import DeviceDB
from bastion_compat.models import Panel, Sensor, Peripheral, Override


class TestDatabaseLoading:
    def test_loads_panels(self, db):
        panels = [d for d in db.all_devices() if d.device_type == "panel"]
        assert len(panels) >= 10

    def test_loads_sensors(self, db):
        sensors = [d for d in db.all_devices() if d.device_type == "sensor"]
        assert len(sensors) >= 20

    def test_loads_peripherals(self, db):
        periphs = [d for d in db.all_devices() if d.device_type == "peripheral"]
        assert len(periphs) >= 5

    def test_loads_overrides(self, db):
        assert len(db.overrides) >= 3

    def test_correct_types(self, db):
        device = db.get("2gig-gc3e")
        assert isinstance(device, Panel)
        device = db.get("honeywell-5811")
        assert isinstance(device, Sensor)
        device = db.get("kwikset-914")
        assert isinstance(device, Peripheral)


class TestDeviceLookup:
    def test_get_existing(self, db):
        device = db.get("2gig-gc3e")
        assert device is not None
        assert device.manufacturer == "2GIG"

    def test_get_nonexistent(self, db):
        assert db.get("nonexistent-device") is None

    def test_all_devices_count(self, db):
        assert len(db.all_devices()) >= 35


class TestSearch:
    def test_search_by_model(self, db):
        results = db.search("5811")
        ids = [d.id for d in results]
        assert "honeywell-5811" in ids

    def test_search_by_manufacturer(self, db):
        results = db.search("Honeywell")
        assert len(results) >= 1
        assert all("honeywell" in d.manufacturer.lower() or "honeywell" in d.model.lower() for d in results[:3])

    def test_search_partial(self, db):
        results = db.search("kwik")
        assert len(results) >= 1

    def test_search_empty(self, db):
        results = db.search("")
        assert results == []


class TestFilter:
    def test_filter_by_type(self, db):
        panels = db.filter(device_type="panel")
        assert all(d.device_type == "panel" for d in panels)
        assert len(panels) >= 10

    def test_filter_by_manufacturer(self, db):
        honeywell = db.filter(manufacturer="Honeywell")
        assert all(d.manufacturer == "Honeywell" for d in honeywell)

    def test_filter_combined(self, db):
        results = db.filter(device_type="sensor", manufacturer="2GIG")
        assert all(d.device_type == "sensor" and d.manufacturer == "2GIG" for d in results)


class TestOverrideLookup:
    def test_find_existing(self, db):
        override = db.find_override("honeywell-5811", "qolsys-iq2-plus")
        assert override is not None
        assert override.verdict == "compatible"

    def test_find_reverse(self, db):
        override = db.find_override("qolsys-iq2-plus", "honeywell-5811")
        assert override is not None

    def test_find_none(self, db):
        override = db.find_override("2gig-gc3e", "kwikset-914")
        assert override is None


class TestExportForClient:
    def test_export_all(self, db):
        exported = db.export_all()
        assert len(exported) >= 35
        for item in exported:
            assert "id" in item
            assert "manufacturer" in item
            assert "model" in item
            assert "device_type" in item
            assert "display_name" in item
