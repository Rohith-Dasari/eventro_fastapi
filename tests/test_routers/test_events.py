import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_event_service
from unittest.mock import MagicMock
from app.models.events import Event
from app.dependencies import get_current_user
from app.custom_exceptions.generic import NotFoundException
from botocore.exceptions import ClientError


class TestEventsRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_get_event_service = MagicMock()
        app.dependency_overrides[get_event_service] = (
            lambda: self.mock_get_event_service
        )
        self.mock_get_current_user = MagicMock()
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "admin",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_create_event_calls_service(self):
        event = Event(
            id="10",
            name="e",
            description="d",
            duration=1,
            category="c",
            is_blocked=False,
            artist_ids=["1"],
            artist_names=["1"],
        )
        self.mock_get_event_service.create_event.return_value = event
        payload = {
            "name": "n",
            "description": "d",
            "duration": 1,
            "category": "movie",
            "artist_ids": ["1"],
        }

        resp = self.client.post("/events", json=payload)

        assert resp.status_code == 201

    def test_get_event_by_id_calls_service(self):
        event = Event(
            id="e1",
            name="e",
            description="d",
            duration=1,
            category="c",
            is_blocked=False,
            artist_ids=["1"],
            artist_names=["1"],
        )
        self.mock_get_event_service.get_event_by_id.return_value = event

        resp = self.client.get("/events/e1")

        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "e"

    def test_browse_events_requires_name_or_city(self):

        resp = self.client.get("/events")

        assert resp.status_code == 422
        assert "At least one of 'name' or 'city'" in resp.text

    def test_browse_events_city_branch(self):
        event = Event(
            id="10",
            name="e",
            description="d",
            duration=1,
            category="c",
            is_blocked=True,
            artist_ids=["1"],
            artist_names=["1"],
        )
        self.mock_get_event_service.browse_events.return_value = [event]

        resp = self.client.get("/events", params={"city": "noida", "is_blocked": True})

        assert resp.status_code == 200

    def test_browse_events_name_branch(self):
        event = Event(
            id="10",
            name="Rock",
            description="d",
            duration=1,
            category="c",
            is_blocked=False,
            artist_ids=["1"],
            artist_names=["1"],
        )
        self.mock_get_event_service.browse_events.return_value = [event]

        resp = self.client.get("/events", params={"name": "Rock", "city": "NYC"})

        assert resp.status_code == 200

    def test_update_event_calls_service(self):
        self.mock_get_event_service.update_event.return_value = None

        resp = self.client.patch("/events/e1", json={"is_blocked": True})
        body = resp.json()
        event_id = "e1"

        assert resp.status_code == 200
        assert body["message"] == f"successfully updated {event_id}"

    def test_create_event_forbidden_role(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "customer",
        }

        resp = self.client.post(
            "/events",
            json={
                "name": "Concert",
                "description": "Live",
                "duration": 120,
                "category": "movie",
                "artist_ids": ["a1"],
            },
        )

        assert resp.status_code == 403
        assert "unauthorised" in resp.text

    def test_get_event_not_found_uses_handler(self):
        self.mock_get_event_service.get_event_by_id.side_effect = NotFoundException(
            resource="event",
            identifier="missing",
            status_code=404,
        )

        resp = self.client.get("/events/missing")

        assert resp.status_code == 404
        assert "missing" in resp.text

    def test_browse_events_name_branch_invokes_service(self):
        event = Event(
            id="10",
            name="Rock",
            description="d",
            duration=1,
            category="c",
            is_blocked=False,
            artist_ids=["1"],
            artist_names=["1"],
        )
        self.mock_get_event_service.browse_events.return_value = [event]

        resp = self.client.get("/events", params={"name": "Rock"})

        assert resp.status_code == 200
