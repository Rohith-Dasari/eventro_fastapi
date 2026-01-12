import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.dependencies import (
    get_show_service,
    get_current_user,
)
from app.custom_exceptions.generic import NotFoundException


class TestShowsRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_show_service = MagicMock()
        app.dependency_overrides[get_show_service] = lambda: self.mock_show_service

        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "host1",
            "role": "host",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_create_show_calls_service(self):
        self.mock_show_service.create_show.return_value = None

        payload = {
            "event_id": "e1",
            "venue_id": "v1",
            "show_date": "2026-01-28",
            "show_time": "18:00",
            "price": "300",
            "host_id": "host1",
        }

        resp = self.client.post("/shows", json=payload)

        assert resp.status_code == 201
        self.mock_show_service.create_show.assert_called_once()

    def test_create_show_forbidden_for_non_host(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "customer",
        }

        resp = self.client.post(
            "/shows",
            json={
                "event_id": "e1",
                "venue_id": "v1",
                "show_date": "2026-01-28",
                "show_time": "18:00",
                "price": "300",
                "host_id": "host1",
            },
        )

        assert resp.status_code == 403
        assert "unauthorised" in resp.text.lower()

    def test_get_show_by_id_calls_service(self):
        self.mock_show_service.get_show_by_id.return_value = {
            "id": "s1",
            "event_id": "e1",
        }

        resp = self.client.get("/shows/s1")

        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == "s1"
        self.mock_show_service.get_show_by_id.assert_called_once_with("s1")

    def test_get_show_by_id_not_found(self):
        self.mock_show_service.get_show_by_id.side_effect = NotFoundException(
            resource="show",
            identifier="missing",
            status_code=404,
        )

        resp = self.client.get("/shows/missing")

        assert resp.status_code == 404
        assert "missing" in resp.text

    def test_event_shows_basic(self):
        self.mock_show_service.get_event_shows.return_value = []

        resp = self.client.get(
            "/shows",
            params={
                "event_id": "e1",
                "city": "delhi",
            },
        )

        assert resp.status_code == 200
        self.mock_show_service.get_event_shows.assert_called_once()

    def test_event_shows_with_host_id_allowed(self):
        self.mock_show_service.get_event_shows.return_value = []

        resp = self.client.get(
            "/shows",
            params={
                "event_id": "e1",
                "city": "delhi",
                "host_id": "host1",
            },
        )

        assert resp.status_code == 200

    def test_event_shows_with_host_id_forbidden(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "other_host",
            "role": "host",
        }

        resp = self.client.get(
            "/shows",
            params={
                "event_id": "e1",
                "city": "delhi",
                "host_id": "host1",
            },
        )
        body = resp.json()

        assert body["status_code"] == 403
        assert "forbidden" in resp.text.lower()

    def test_update_show_calls_service(self):
        self.mock_show_service.update_show.return_value = None

        resp = self.client.patch(
            "/shows/s1",
            json={
                "price": "500",
                "is_blocked": True,
            },
        )

        assert resp.status_code == 200
        self.mock_show_service.update_show.assert_called_once()

    def test_update_show_forbidden_for_non_host(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "customer",
        }

        resp = self.client.patch(
            "/shows/s1",
            json={"price": "500"},
        )

        assert resp.status_code == 403
