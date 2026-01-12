import unittest
from unittest.mock import MagicMock

from app.services.booking_service import BookingService
from app.schemas.booking import BookingReq
from app.models.shows import Show
from app.models.venue import Venue
from app.models.events import Event
from app.custom_exceptions.generic import BlockedResource


class TestBookingService(unittest.TestCase):

    def setUp(self):
        self.mock_booking_repo = MagicMock()
        self.mock_show_repo = MagicMock()
        self.mock_event_repo = MagicMock()
        self.mock_venue_repo = MagicMock()

        self.booking_service = BookingService(
            booking_repo=self.mock_booking_repo,
            show_repo=self.mock_show_repo,
            event_repo=self.mock_event_repo,
            venue_repo=self.mock_venue_repo,
        )

    def _valid_show(self, booked_seats=None):
        return Show(
            id="s1",
            venue_id="v1",
            event_id="e1",
            is_blocked=False,
            price=300,
            show_date="2026-01-28",
            show_time="18:00",
            booked_seats=booked_seats or [],
        )

    def _valid_event(self, is_blocked=False):
        return Event(
            id="e1",
            name="Movie",
            description="d",
            duration="120",
            category="movie",
            is_blocked=is_blocked,
            artist_ids=[],
            artist_names=[],
        )

    def _valid_venue(self, is_blocked=False):
        return Venue(
            id="v1",
            name="PVR",
            city="delhi",
            state="delhi",
            host_id="host1",
            is_blocked=is_blocked,
            is_seat_layout_required=True,
        )

    def test_create_booking_success(self):
        req = BookingReq(show_id="s1", seats=["A1", "A2"])

        self.mock_show_repo.get_show_by_id.return_value = self._valid_show()
        self.mock_event_repo.get_by_id.return_value = self._valid_event()
        self.mock_venue_repo.get_venue_by_id.return_value = self._valid_venue()

        booking = self.booking_service.create_booking(req, user_id="u1")

        assert booking.total_price == 600
        assert booking.seats == ["A1", "A2"]
        assert booking.venue_name == "PVR"

        self.mock_booking_repo.add_booking.assert_called_once()

    def test_create_booking_blocked_show(self):
        req = BookingReq(show_id="s1", seats=["A1"])

        blocked_show = MagicMock(is_blocked=True, id="s1")
        self.mock_show_repo.get_show_by_id.return_value = blocked_show

        with self.assertRaises(BlockedResource):
            self.booking_service.create_booking(req, user_id="u1")

    def test_create_booking_blocked_event(self):
        req = BookingReq(show_id="s1", seats=["A1"])

        self.mock_show_repo.get_show_by_id.return_value = self._valid_show()
        self.mock_event_repo.get_by_id.return_value = self._valid_event(is_blocked=True)

        with self.assertRaises(BlockedResource):
            self.booking_service.create_booking(req, user_id="u1")

    def test_create_booking_blocked_venue(self):
        req = BookingReq(show_id="s1", seats=["A1"])

        self.mock_show_repo.get_show_by_id.return_value = self._valid_show()
        self.mock_event_repo.get_by_id.return_value = self._valid_event()
        self.mock_venue_repo.get_venue_by_id.return_value = self._valid_venue(
            is_blocked=True
        )

        with self.assertRaises(BlockedResource):
            self.booking_service.create_booking(req, user_id="u1")

    def test_create_booking_seat_already_booked(self):
        req = BookingReq(show_id="s1", seats=["A1"])

        show = self._valid_show(booked_seats=["A1"])
        self.mock_show_repo.get_show_by_id.return_value = show

        with self.assertRaises(Exception):
            self.booking_service.create_booking(req, user_id="u1")

    def test_get_user_bookings(self):
        bookings = [MagicMock(), MagicMock()]
        self.mock_booking_repo.get_bookings.return_value = bookings

        result = self.booking_service.get_user_bookings("u1")

        assert result == bookings
        self.mock_booking_repo.get_bookings.assert_called_once_with(user_id="u1")
