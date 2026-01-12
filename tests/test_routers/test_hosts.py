import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.dependencies import (
    get_venue_service,
    get_event_service,
    get_current_user,
)
from fastapi import HTTPException


class TestHostsRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_venue_service = MagicMock()
        self.mock_event_service = MagicMock()

        app.dependency_overrides[get_venue_service] = lambda: self.mock_venue_service
        app.dependency_overrides[get_event_service] = lambda: self.mock_event_service

        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "host1",
            "role": "host",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_host_venues_as_host(self):
        self.mock_venue_service.get_host_venues.return_value = [
            {"venue_id": "v1"},
            {"venue_id": "v2"},
        ]

        resp = self.client.get("/hosts/host1/venues")

        assert resp.status_code == 200
        body = resp.json()

        assert len(body["data"]) == 2
        self.mock_venue_service.get_host_venues.assert_called_once_with(
            host_id="host1", is_blocked=None
        )

    def test_get_host_venues_with_is_blocked_filter(self):
        self.mock_venue_service.get_host_venues.return_value = []

        resp = self.client.get("/hosts/host1/venues", params={"is_blocked": True})

        assert resp.status_code == 200
        self.mock_venue_service.get_host_venues.assert_called_once_with(
            host_id="host1", is_blocked=True
        )

    def test_get_host_venues_as_admin(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "admin1",
            "role": "admin",
        }

        self.mock_venue_service.get_host_venues.return_value = []

        resp = self.client.get("/hosts/host1/venues")

        assert resp.status_code == 200

    def test_get_host_venues_forbidden_for_other_host(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "host2",
            "role": "host",
        }

        resp = self.client.get("/hosts/host1/venues")

        assert resp.status_code == 401
        assert "not authorised" in resp.text.lower()

    # -------------------- HOST EVENTS --------------------

    def test_get_host_events_as_host(self):
        self.mock_event_service.get_host_events.return_value = [
            {"event_id": "e1"},
            {"event_id": "e2"},
        ]

        resp = self.client.get("/hosts/host1/events")

        assert resp.status_code == 200
        body = resp.json()

        assert len(body["data"]) == 2
        self.mock_event_service.get_host_events.assert_called_once_with(host_id="host1")

    def test_get_host_events_as_admin(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "admin1",
            "role": "admin",
        }

        self.mock_event_service.get_host_events.return_value = []

        resp = self.client.get("/hosts/host1/events")

        assert resp.status_code == 200

    def test_get_host_events_forbidden_for_other_host(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "host2",
            "role": "host",
        }

        resp = self.client.get("/hosts/host1/events")

        assert resp.status_code == 401
        assert "not authorised" in resp.text.lower()
