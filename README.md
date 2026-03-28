# BASTION Device Compatibility Checker

Check if your home security devices are compatible before you buy. 403 devices across 45 manufacturers with 79 field-tested compatibility overrides. Frequency matching, protocol validation, and known edge cases — so you don't find out after the install.

Built on a decade of home security industry experience.

Part of the [BASTION](https://github.com/Pachacutie/BASTION) portfolio.

---

## Use It Online

No install needed. Open in your browser, pick two devices, get your answer:

**[bastion-compat-check.onrender.com](https://bastion-compat-check.onrender.com)**

No data stored. No accounts. No tracking. Compatibility checks run in memory and return a result — nothing is logged.

---

## Run It Locally (Complete Privacy)

For maximum privacy, install and run on your own computer. No network calls, no telemetry.

### Install

Requires Python 3.12+.

```bash
pip install bastion-compat-check
```

### Launch the Web Interface

```bash
flask --app src.bastion_compat.web:create_app run
```

Opens the same interface — running entirely on your machine.

---

## What It Does

Select two devices — a panel and a sensor (or peripheral) — and get an instant compatibility verdict:

| Verdict | Meaning |
|---------|---------|
| **COMPATIBLE** | Devices work together. Frequency and protocol confirmed. |
| **INCOMPATIBLE** | Devices will not work together. |
| **PARTIAL** | Devices can connect but with limitations (e.g., reduced feature set). |
| **UNKNOWN** | Not enough data to determine compatibility. |

### Features

- **Two-device compatibility check** — select any two devices and get an instant verdict with explanation
- **Single-device mode** — select one device to see everything compatible with it
- **Browsable device database** — filterable table of all 403 devices
- **Dynamic alternatives** — incompatible verdicts suggest compatible alternatives
- **Search-as-you-type** — find devices by manufacturer, model, or type

## Device Database

**403 devices** across **45 manufacturers** with **79 compatibility overrides**.

Top manufacturers: Honeywell (59), 2GIG (47), Frontpoint (39), Interlogix/GE (34), Resolution Products/Alula (34), Ring (16), SimpliSafe (16), Alarm.com (16), Vivint (14), DSC (12), Elk Products (12), Yale (11), Abode (10), Qolsys (9), Cove (9), ADT (5), and 29 more.

**Peripheral categories:** Smart locks, thermostats, cameras, garage controllers, water valves, sirens, keypads, Z-Wave switches/dimmers, repeaters, receivers, and translators.

Database grows via community contribution. See [Contributing Device Data](#contributing-device-data) below.

## How It Works

The rules engine evaluates devices in priority order:

1. **Explicit overrides** — field-tested compatibility data takes precedence over rules
2. **Frequency match** — sensor RF frequency must match the panel's receiver
3. **Protocol match** — Z-Wave to Z-Wave, proprietary RF to proprietary RF
4. **Partial compatibility** — Z-Wave Plus device on a Z-Wave (non-Plus) controller
5. **Platform dependency** — flags when a device requires a specific monitoring platform

No AI, no cloud, no network calls. Pure rule evaluation against a curated device database.

## Development

```bash
git clone https://github.com/Pachacutie/bastion-compat-check.git
cd bastion-compat-check
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev,web]"
pytest -v
```

## Contributing Device Data

Edit the JSON files in `data/` and submit a PR:

- `panels.json` — control panels and hubs
- `sensors.json` — door/window, motion, glass break, smoke, CO, flood, etc.
- `peripherals.json` — locks, thermostats, garage controllers, cameras, water valves
- `overrides.json` — known edge cases that rules alone can't catch

Each entry follows a strict JSON schema. See existing entries for format.

## License

MIT
