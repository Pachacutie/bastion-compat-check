"""Tests for the Flask web interface."""

import json

import pytest

from bastion_compat.web import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestIndexPage:
    def test_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"BASTION" in resp.data

    def test_contains_search_ui(self, client):
        resp = client.get("/")
        assert b"Device" in resp.data


class TestDevicesAPI:
    def test_returns_json(self, client):
        resp = client.get("/api/devices")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) >= 35

    def test_device_fields(self, client):
        resp = client.get("/api/devices")
        data = json.loads(resp.data)
        for item in data:
            assert "id" in item
            assert "display_name" in item
            assert "device_type" in item


class TestCheckAPI:
    def test_compatible_pair(self, client):
        resp = client.post(
            "/api/check",
            json={"device_a": "2gig-dw10", "device_b": "2gig-gc3e"},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["verdict"] in ("COMPATIBLE", "PARTIAL")

    def test_incompatible_pair(self, client):
        resp = client.post(
            "/api/check",
            json={"device_a": "dsc-pg9303", "device_b": "2gig-gc3e"},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["verdict"] == "INCOMPATIBLE"

    def test_unknown_device(self, client):
        resp = client.post(
            "/api/check",
            json={"device_a": "fake", "device_b": "2gig-gc3e"},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["verdict"] == "UNKNOWN"

    def test_missing_params(self, client):
        resp = client.post("/api/check", json={"device_a": "2gig-gc3e"})
        assert resp.status_code == 400

    def test_same_device(self, client):
        resp = client.post(
            "/api/check",
            json={"device_a": "2gig-gc3e", "device_b": "2gig-gc3e"},
        )
        assert resp.status_code == 400


class TestSingleDeviceAPI:
    def test_returns_compatible_list(self, client):
        resp = client.get("/api/compatible/2gig-gc3e")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data) >= 1
        for item in data:
            assert item["verdict"] in ("COMPATIBLE", "PARTIAL")

    def test_unknown_device(self, client):
        resp = client.get("/api/compatible/nonexistent")
        assert resp.status_code == 404
