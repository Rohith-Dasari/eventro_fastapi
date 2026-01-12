import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.dependencies import get_booking_service, get_current_user
from app.custom_exceptions.generic import NotFoundException
from app.schemas.booking import BookingReq


class TestBookingsRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_booking_service = MagicMock()
        app.dependency_overrides[get_booking_service] = (
            lambda: self.mock_booking_service
        )

        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "customer",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_create_booking_calls_service(self):
        self.mock_booking_service.create_booking.return_value = {
            "booking_id": "b1",
            "show_id": "s1",
            "user_id": "u1",
            "seats": ["A1", "A2"],
        }

        payload = {
            "show_id": "s1",
            "seats": ["A1", "A2"],
        }

        resp = self.client.post("/bookings", json=payload)

        assert resp.status_code == 200
        body = resp.json()

        assert body["message"] == "succesfully made booking"
        assert body["data"]["booking_id"] == "b1"

        self.mock_booking_service.create_booking.assert_called_once_with(
            BookingReq(show_id="s1", seats=["A1", "A2"]), "u1"
        )

    def test_create_booking_propagates_not_found(self):
        self.mock_booking_service.create_booking.side_effect = NotFoundException(
            resource="show",
            identifier="missing",
            status_code=404,
        )

        payload = {
            "show_id": "missing",
            "seats": ["A1"],
        }

        resp = self.client.post("/bookings", json=payload)

        assert resp.status_code == 404
        assert "missing" in resp.text
