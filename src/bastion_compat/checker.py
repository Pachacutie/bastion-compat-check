"""Compatibility rules engine."""

from __future__ import annotations

from .database import DeviceDB
from .models import (
    CompatResult,
    Device,
    Override,
    Panel,
    Peripheral,
    Sensor,
    VerdictType,
)

# Z-Wave protocol compatibility matrix
_ZWAVE_COMPAT = {
    ("zwave", "zwave"): VerdictType.COMPATIBLE,
    ("zwave", "zwave_plus"): VerdictType.COMPATIBLE,
    ("zwave_plus", "zwave"): VerdictType.COMPATIBLE,
    ("zwave_plus", "zwave_plus"): VerdictType.COMPATIBLE,
}


def check_compatibility(
    id_a: str, id_b: str, db: DeviceDB, *, _skip_alternatives: bool = False
) -> CompatResult:
    """Check compatibility between two devices."""
    device_a = db.get(id_a)
    device_b = db.get(id_b)

    # Rule 1: Unknown device — exit early before any data access
    if device_a is None or device_b is None:
        missing = []
        if device_a is None:
            missing.append(id_a)
        if device_b is None:
            missing.append(id_b)
        return CompatResult(
            verdict=VerdictType.UNKNOWN,
            explanation=f"Device(s) not in database: {', '.join(missing)}. "
            "Check manufacturer specs for frequency and protocol compatibility, "
            "or contribute data via GitHub.",
        )

    # Rule 2: Override check — explicit data wins
    override = db.find_override(id_a, id_b)
    if override:
        return _from_override(override, device_a, device_b, db, _skip_alternatives)

    # Identify the panel
    panel, other = _identify_panel(device_a, device_b)
    if panel is None:
        return _check_non_panel_pair(device_a, device_b, db)

    if isinstance(other, Sensor):
        return _check_sensor_panel(other, panel, db, _skip_alternatives)
    elif isinstance(other, Peripheral):
        return _check_peripheral_panel(other, panel, db, _skip_alternatives)

    return CompatResult(
        verdict=VerdictType.UNKNOWN,
        explanation="Unable to determine compatibility for this device combination.",
    )


def find_compatible_devices(
    device_id: str, db: DeviceDB
) -> list[tuple[str, CompatResult]]:
    """Find all devices compatible with the given device."""
    device = db.get(device_id)
    if device is None:
        return []

    results = []
    for other in db.all_devices():
        if other.id == device_id:
            continue
        result = check_compatibility(device_id, other.id, db, _skip_alternatives=True)
        if result.verdict in (VerdictType.COMPATIBLE, VerdictType.PARTIAL):
            results.append((other.id, result))
    return results


def _from_override(
    override: Override, device_a: Device, device_b: Device, db: DeviceDB,
    skip_alternatives: bool = False,
) -> CompatResult:
    """Build CompatResult from an explicit override."""
    verdict = VerdictType(override.verdict.upper())
    requirements = [override.condition] if override.condition else []
    alternatives_display = []
    for alt_id in override.alternatives:
        alt = db.get(alt_id)
        if alt:
            alternatives_display.append(f"{alt.display_name} ({alt.id})")
        else:
            alternatives_display.append(alt_id)

    if verdict == VerdictType.INCOMPATIBLE and not alternatives_display and not skip_alternatives:
        alternatives_display = _find_alternatives(device_a, device_b, db)

    if verdict == VerdictType.COMPATIBLE:
        explanation = f"{device_a.display_name} is compatible with {device_b.display_name}."
    elif verdict == VerdictType.INCOMPATIBLE:
        explanation = (
            f"{device_a.display_name} is not compatible with {device_b.display_name}."
            + (f" {override.condition}" if override.condition else "")
        )
    else:
        explanation = f"{device_a.display_name} has limited compatibility with {device_b.display_name}."

    return CompatResult(
        verdict=verdict,
        explanation=explanation,
        requirements=requirements,
        limitations=list(override.limitations),
        alternatives=alternatives_display,
    )


def _identify_panel(a: Device, b: Device) -> tuple[Panel | None, Device | None]:
    """Return (panel, other) or (None, None) if no panel."""
    if isinstance(a, Panel):
        return a, b
    if isinstance(b, Panel):
        return b, a
    return None, None


def _check_non_panel_pair(a: Device, b: Device, db: DeviceDB) -> CompatResult:
    return CompatResult(
        verdict=VerdictType.UNKNOWN,
        explanation=f"Neither {a.display_name} nor {b.display_name} is a control panel. "
        "Sensors and peripherals typically connect to a panel, not to each other.",
    )


def _check_sensor_panel(
    sensor: Sensor, panel: Panel, db: DeviceDB, skip_alternatives: bool = False,
) -> CompatResult:
    """Rules 2-5 for sensor + panel."""
    # Check if sensor uses Z-Wave (not RF frequency)
    if sensor.protocol in ("zwave", "zwave_plus"):
        return _check_zwave_device_panel(sensor, panel, sensor.protocol, db, skip_alternatives)

    # Rule 2: Frequency match (for RF sensors)
    if sensor.frequency and sensor.frequency not in panel.frequencies:
        return CompatResult(
            verdict=VerdictType.INCOMPATIBLE,
            explanation=f"The {sensor.display_name} operates at {sensor.frequency}. "
            f"The {panel.display_name} supports {', '.join(panel.frequencies) or 'no RF frequencies'}. "
            "These frequencies are not compatible.",
            alternatives=_find_alternatives(sensor, panel, db) if not skip_alternatives else [],
        )

    # Rule 3: Protocol match (for RF sensors)
    if sensor.protocol and sensor.protocol not in panel.protocols:
        return CompatResult(
            verdict=VerdictType.INCOMPATIBLE,
            explanation=f"The {sensor.display_name} uses {sensor.protocol} protocol. "
            f"The {panel.display_name} supports {', '.join(panel.protocols)}. "
            "These protocols are not compatible.",
            alternatives=_find_alternatives(sensor, panel, db) if not skip_alternatives else [],
        )

    # Compatible — add platform requirements
    requirements = _platform_requirements(panel)
    return CompatResult(
        verdict=VerdictType.COMPATIBLE,
        explanation=f"The {sensor.display_name} ({sensor.frequency}, {sensor.protocol}) "
        f"is compatible with the {panel.display_name}.",
        requirements=requirements,
    )


def _check_peripheral_panel(
    peripheral: Peripheral, panel: Panel, db: DeviceDB,
    skip_alternatives: bool = False,
) -> CompatResult:
    """Rules 3-5 for peripheral + panel."""
    # Find protocol overlap (including Z-Wave cross-compat)
    shared = set(peripheral.protocols) & set(panel.protocols)

    if not shared:
        for p_proto in peripheral.protocols:
            zwave_result = _check_zwave_compat(p_proto, panel.protocols)
            if zwave_result is not None:
                shared.add(p_proto)
                break

    if not shared:
        return CompatResult(
            verdict=VerdictType.INCOMPATIBLE,
            explanation=f"The {peripheral.display_name} uses {', '.join(peripheral.protocols)}. "
            f"The {panel.display_name} supports {', '.join(panel.protocols)}. "
            "No shared protocol found.",
            alternatives=_find_alternatives(peripheral, panel, db) if not skip_alternatives else [],
        )

    # Rule 4: Z-Wave / Z-Wave Plus partial detection
    limitations = []
    verdict = VerdictType.COMPATIBLE
    for p_proto in peripheral.protocols:
        for panel_proto in panel.protocols:
            if p_proto == "zwave_plus" and panel_proto == "zwave" and "zwave_plus" not in panel.protocols:
                verdict = VerdictType.PARTIAL
                limitations.append(
                    "Z-Wave Plus device on Z-Wave controller — reduced range and speed"
                )

    requirements = _platform_requirements(panel)
    return CompatResult(
        verdict=verdict,
        explanation=f"The {peripheral.display_name} connects to the "
        f"{panel.display_name} via {', '.join(shared)}.",
        requirements=requirements,
        limitations=limitations,
    )


def _check_zwave_device_panel(
    device: Device, panel: Panel, device_proto: str, db: DeviceDB,
    skip_alternatives: bool = False,
) -> CompatResult:
    """Check Z-Wave sensor/peripheral against panel."""
    zwave_result = _check_zwave_compat(device_proto, panel.protocols)
    if zwave_result is None:
        return CompatResult(
            verdict=VerdictType.INCOMPATIBLE,
            explanation=f"The {device.display_name} uses {device_proto}. "
            f"The {panel.display_name} supports {', '.join(panel.protocols)}. "
            "No Z-Wave support on this panel.",
            alternatives=_find_alternatives(device, panel, db) if not skip_alternatives else [],
        )

    limitations = []
    verdict = VerdictType.COMPATIBLE
    if device_proto == "zwave_plus" and "zwave_plus" not in panel.protocols and "zwave" in panel.protocols:
        verdict = VerdictType.PARTIAL
        limitations.append("Z-Wave Plus device on Z-Wave controller — reduced range and speed")

    requirements = _platform_requirements(panel)
    return CompatResult(
        verdict=verdict,
        explanation=f"The {device.display_name} connects to the {panel.display_name} via Z-Wave.",
        requirements=requirements,
        limitations=limitations,
    )


def _check_zwave_compat(device_proto: str, panel_protos: list[str]) -> VerdictType | None:
    """Check if device protocol has Z-Wave compatibility with any panel protocol."""
    for panel_proto in panel_protos:
        key = (device_proto, panel_proto)
        if key in _ZWAVE_COMPAT:
            return _ZWAVE_COMPAT[key]
    return None


def _platform_requirements(panel: Panel) -> list[str]:
    platforms = {
        "alarm_com": "Full functionality requires an Alarm.com account",
        "honeywell_total_connect": "Full functionality requires Honeywell Total Connect",
        "vivint_platform": "Full functionality requires Vivint platform subscription",
        "ring_platform": "Full functionality requires Ring Protect subscription",
    }
    if panel.platform:
        return [platforms.get(panel.platform, f"Full functionality may require {panel.platform} platform")]
    return []


def _find_alternatives(device: Device, target: Device, db: DeviceDB) -> list[str]:
    """Find same-type devices compatible with the target. Max 3."""
    panel = target if isinstance(target, Panel) else (device if isinstance(device, Panel) else None)
    non_panel = device if not isinstance(device, Panel) else target

    if panel is None:
        return []

    alternatives = []
    for candidate in db.all_devices():
        if candidate.id == non_panel.id:
            continue
        if candidate.device_type != non_panel.device_type:
            continue
        result = check_compatibility(candidate.id, panel.id, db, _skip_alternatives=True)
        if result.verdict in (VerdictType.COMPATIBLE, VerdictType.PARTIAL):
            alternatives.append(f"{candidate.display_name} ({candidate.id})")
        if len(alternatives) >= 3:
            break
    return alternatives
