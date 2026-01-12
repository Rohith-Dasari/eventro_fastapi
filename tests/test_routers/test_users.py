import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.dependencies import (
    get_user_service,
    get_booking_service,
    get_current_user,
)
from app.custom_exceptions.generic import NotFoundException


class TestUsersRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_user_service = MagicMock()
        self.mock_booking_service = MagicMock()

        app.dependency_overrides[get_user_service] = lambda: self.mock_user_service
        app.dependency_overrides[get_booking_service] = (
            lambda: self.mock_booking_service
        )

        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "customer",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_user_profile_calls_service(self):
        self.mock_user_service.get_user_profile.return_value = {
            "user_id": "u1",
            "name": "Rohith",
        }

        resp = self.client.get("/users/u1")

        assert resp.status_code == 200
        body = resp.json()

        assert body["data"]["user_id"] == "u1"
        self.mock_user_service.get_user_profile.assert_called_once_with("u1")

    def test_get_user_profile_not_found(self):
        self.mock_user_service.get_user_profile.side_effect = NotFoundException(
            resource="user",
            identifier="u1",
            status_code=404,
        )

        resp = self.client.get("/users/u1")

        assert resp.status_code == 404
        assert "u1" in resp.text

    def test_get_user_bookings_calls_service(self):
        self.mock_booking_service.get_user_bookings.return_value = [
            {"booking_id": "b1"},
            {"booking_id": "b2"},
        ]

        resp = self.client.get("/users/u1/bookings")

        assert resp.status_code == 200
        body = resp.json()

        assert len(body["data"]) == 2
        self.mock_booking_service.get_user_bookings.assert_called_once_with("u1")

    def test_get_user_bookings_empty(self):
        self.mock_booking_service.get_user_bookings.return_value = []

        resp = self.client.get("/users/u1/bookings")

        assert resp.status_code == 200
        assert resp.json()["data"] == []
