"""Tests for data models."""

from bastion_compat.models import (
    CompatResult,
    Override,
    Panel,
    Peripheral,
    Sensor,
    VerdictType,
)


class TestPanel:
    def test_device_type(self):
        p = Panel(
            id="2gig-gc3e",
            manufacturer="2GIG",
            model="GC3e",
            frequencies=["319.5MHz", "345MHz"],
            protocols=["proprietary_rf", "zwave_plus"],
            platform="alarm_com",
        )
        assert p.device_type == "panel"

    def test_display_name(self):
        p = Panel(
            id="2gig-gc3e",
            manufacturer="2GIG",
            model="GC3e",
            frequencies=["319.5MHz", "345MHz"],
            protocols=["proprietary_rf", "zwave_plus"],
        )
        assert p.display_name == "2GIG GC3e"

    def test_frequencies_required(self):
        p = Panel(
            id="test",
            manufacturer="Test",
            model="T1",
            frequencies=["345MHz"],
            protocols=["proprietary_rf"],
        )
        assert p.frequencies == ["345MHz"]


class TestSensor:
    def test_device_type(self):
        s = Sensor(
            id="honeywell-5811",
            manufacturer="Honeywell",
            model="5811",
            sensor_type="door_window",
            frequency="345MHz",
            protocol="proprietary_rf",
        )
        assert s.device_type == "sensor"

    def test_display_name(self):
        s = Sensor(
            id="honeywell-5811",
            manufacturer="Honeywell",
            model="5811",
            sensor_type="door_window",
            frequency="345MHz",
            protocol="proprietary_rf",
        )
        assert s.display_name == "Honeywell 5811"


class TestPeripheral:
    def test_device_type(self):
        p = Peripheral(
            id="kwikset-914",
            manufacturer="Kwikset",
            model="914",
            peripheral_type="smart_lock",
            protocols=["zwave"],
        )
        assert p.device_type == "peripheral"

    def test_protocols_list(self):
        p = Peripheral(
            id="kwikset-914",
            manufacturer="Kwikset",
            model="914",
            peripheral_type="smart_lock",
            protocols=["zwave", "bluetooth"],
        )
        assert "zwave" in p.protocols


class TestOverride:
    def test_matches_forward(self):
        o = Override(
            device_a="honeywell-5811",
            device_b="qolsys-iq2-plus",
            verdict="compatible",
            condition="Requires 345MHz daughtercard",
        )
        assert o.matches("honeywell-5811", "qolsys-iq2-plus")

    def test_matches_reverse(self):
        o = Override(
            device_a="honeywell-5811",
            device_b="qolsys-iq2-plus",
            verdict="compatible",
            condition="Requires 345MHz daughtercard",
        )
        assert o.matches("qolsys-iq2-plus", "honeywell-5811")

    def test_no_match(self):
        o = Override(
            device_a="honeywell-5811",
            device_b="qolsys-iq2-plus",
            verdict="compatible",
            condition="test",
        )
        assert not o.matches("honeywell-5811", "ring-alarm-pro")


class TestVerdict:
    def test_enum_values(self):
        assert VerdictType.COMPATIBLE == "COMPATIBLE"
        assert VerdictType.INCOMPATIBLE == "INCOMPATIBLE"
        assert VerdictType.PARTIAL == "PARTIAL"
        assert VerdictType.UNKNOWN == "UNKNOWN"

    def test_compat_result(self):
        r = CompatResult(
            verdict=VerdictType.COMPATIBLE,
            explanation="These devices work together.",
        )
        assert r.verdict == VerdictType.COMPATIBLE
        assert r.requirements == []
        assert r.limitations == []
        assert r.alternatives == []
