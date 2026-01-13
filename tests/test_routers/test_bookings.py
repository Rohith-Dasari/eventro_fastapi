import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.dependencies import (
    get_booking_service,
    get_current_user,
    get_user_service,
)
from app.custom_exceptions.generic import NotFoundException
from app.schemas.booking import BookingReq
from app.models.users import Role


class TestBookingsRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_booking_service = MagicMock()
        self.mock_user_service = MagicMock()

        app.dependency_overrides[get_booking_service] = (
            lambda: self.mock_booking_service
        )
        app.dependency_overrides[get_user_service] = lambda: self.mock_user_service

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_create_booking_customer(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": Role.CUSTOMER.value,
        }

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

        assert resp.status_code == 201
        body = resp.json()

        assert body["message"] == "succesfully made booking"
        assert body["data"]["booking_id"] == "b1"

        self.mock_booking_service.create_booking.assert_called_once_with(
            BookingReq(show_id="s1", seats=["A1", "A2"]),
            "u1",
        )

        self.mock_user_service.get_user_by_mail.assert_not_called()

    def test_create_booking_admin(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "admin1",
            "role": Role.ADMIN.value,
        }

        mock_user = MagicMock()
        mock_user.user_id = "u99"
        self.mock_user_service.get_user_by_mail.return_value = mock_user

        self.mock_booking_service.create_booking.return_value = {
            "booking_id": "b2",
            "show_id": "s1",
            "user_id": "u99",
            "seats": ["A1"],
        }

        payload = {
            "show_id": "s1",
            "seats": ["A1"],
            "user_id": "user@mail.com",
        }

        resp = self.client.post("/bookings", json=payload)

        assert resp.status_code == 201

        self.mock_user_service.get_user_by_mail.assert_called_once_with(
            mail="user@mail.com"
        )

        self.mock_booking_service.create_booking.assert_called_once_with(
            BookingReq(show_id="s1", seats=["A1"], user_id="user@mail.com"),
            "u99",
        )

    def test_create_booking_propagates_not_found(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": Role.CUSTOMER.value,
        }

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
