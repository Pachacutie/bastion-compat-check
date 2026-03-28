"""Tests for the compatibility rules engine."""

from bastion_compat.checker import check_compatibility, find_compatible_devices
from bastion_compat.models import VerdictType


class TestOverrideRule:
    """Rule 1: Explicit overrides take precedence."""

    def test_compatible_override(self, db):
        result = check_compatibility("honeywell-5811", "qolsys-iq2-plus", db)
        assert result.verdict == VerdictType.COMPATIBLE
        assert any("daughtercard" in r.lower() for r in result.requirements) or "daughtercard" in result.explanation.lower()

    def test_incompatible_override(self, db):
        result = check_compatibility("honeywell-5800pir", "ring-alarm-gen2", db)
        assert result.verdict == VerdictType.INCOMPATIBLE

    def test_override_limitations(self, db):
        result = check_compatibility("honeywell-5811", "qolsys-iq2-plus", db)
        assert len(result.limitations) >= 1

    def test_override_alternatives(self, db):
        result = check_compatibility("honeywell-5800pir", "ring-alarm-gen2", db)
        assert len(result.alternatives) >= 1


class TestFrequencyMatch:
    """Rule 2: Sensor frequency must match panel frequencies."""

    def test_matching_frequency(self, db):
        # 2GIG DW10 (319.5MHz) + 2GIG GC3e (319.5MHz, 345MHz) = should be compatible
        result = check_compatibility("2gig-dw10", "2gig-gc3e", db)
        assert result.verdict in (VerdictType.COMPATIBLE, VerdictType.PARTIAL)

    def test_mismatched_frequency(self, db):
        # DSC PG9303 (433MHz) + 2GIG GC3e (319.5MHz, 345MHz) = incompatible
        result = check_compatibility("dsc-pg9303", "2gig-gc3e", db)
        assert result.verdict == VerdictType.INCOMPATIBLE
        assert "frequency" in result.explanation.lower() or "MHz" in result.explanation


class TestProtocolMatch:
    """Rule 3: Protocol must be compatible."""

    def test_zwave_peripheral_with_zwave_panel(self, db):
        # Kwikset 914 (zwave) + 2GIG GC3e (zwave_plus) = compatible (not partial)
        result = check_compatibility("kwikset-914", "2gig-gc3e", db)
        assert result.verdict == VerdictType.COMPATIBLE

    def test_zwave_peripheral_with_rf_only_panel(self, db):
        # Kwikset 914 (zwave) + Honeywell Vista 20P (proprietary_rf only) = incompatible
        result = check_compatibility("kwikset-914", "honeywell-vista-20p", db)
        assert result.verdict == VerdictType.INCOMPATIBLE


class TestPartialCompatibility:
    """Rule 4: Devices connect but with limitations."""

    def test_partial_override(self, db):
        result = check_compatibility("kwikset-914", "2gig-gc2", db)
        assert result.verdict == VerdictType.PARTIAL
        assert len(result.limitations) >= 1


class TestPlatformDependency:
    """Rule 5: Flag cloud platform requirements."""

    def test_alarm_com_platform(self, db):
        result = check_compatibility("2gig-dw10", "2gig-gc3e", db)
        all_text = result.explanation + " ".join(result.requirements)
        assert "alarm.com" in all_text.lower() or "platform" in all_text.lower()


class TestNonPanelPair:
    """Two non-panel devices return UNKNOWN."""

    def test_two_sensors(self, db):
        result = check_compatibility("honeywell-5811", "2gig-dw10", db)
        assert result.verdict == VerdictType.UNKNOWN

    def test_sensor_and_peripheral(self, db):
        result = check_compatibility("honeywell-5811", "kwikset-914", db)
        assert result.verdict == VerdictType.UNKNOWN


class TestUnknownDevice:
    """Rule 1: Unknown devices return UNKNOWN verdict."""

    def test_one_unknown(self, db):
        result = check_compatibility("nonexistent-device", "2gig-gc3e", db)
        assert result.verdict == VerdictType.UNKNOWN

    def test_both_unknown(self, db):
        result = check_compatibility("fake-a", "fake-b", db)
        assert result.verdict == VerdictType.UNKNOWN


class TestDynamicAlternatives:
    """INCOMPATIBLE verdicts should suggest compatible alternatives."""

    def test_alternatives_for_incompatible(self, db):
        # DSC sensor (433MHz) + 2GIG panel (319.5/345MHz) = incompatible
        result = check_compatibility("dsc-pg9303", "2gig-gc3e", db)
        assert result.verdict == VerdictType.INCOMPATIBLE
        assert len(result.alternatives) >= 1


class TestSingleDeviceMode:
    def test_find_compatible_devices(self, db):
        results = find_compatible_devices("2gig-gc3e", db)
        assert len(results) >= 1
        for device_id, compat in results:
            assert compat.verdict in (VerdictType.COMPATIBLE, VerdictType.PARTIAL)

    def test_unknown_device(self, db):
        results = find_compatible_devices("nonexistent", db)
        assert results == []

    def test_no_self_match(self, db):
        results = find_compatible_devices("2gig-gc3e", db)
        ids = [device_id for device_id, _ in results]
        assert "2gig-gc3e" not in ids
