"""Shared test fixtures."""

from pathlib import Path

import pytest

from bastion_compat.database import DeviceDB

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def db() -> DeviceDB:
    return DeviceDB(DATA_DIR)
