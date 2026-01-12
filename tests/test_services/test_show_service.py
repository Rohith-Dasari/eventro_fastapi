import unittest
from unittest.mock import MagicMock

from app.services.show_service import ShowService
from app.models.shows import Show
from app.models.venue import Venue
from app.models.events import Event
from app.schemas.shows import ShowCreateReq, ShowUpdateReq
from app.custom_exceptions.generic import NotFoundException
from app.models.users import Role


class TestShowService(unittest.TestCase):

    def setUp(self):
        self.mock_show_repo = MagicMock()
        self.mock_venue_repo = MagicMock()
        self.mock_event_repo = MagicMock()

        self.show_service = ShowService(
            show_repo=self.mock_show_repo,
            venue_repo=self.mock_venue_repo,
            event_repo=self.mock_event_repo,
        )

    def test_create_show_success(self):
        req = ShowCreateReq(
            venue_id="v1",
            event_id="e1",
            price="300",
            show_date="2026-01-28",
            show_time="18:00",
        )

        venue = Venue(
            id="v1",
            name="PVR",
            city="delhi",
            state="delhi",
            host_id="host1",
            is_blocked=False,
            is_seat_layout_required=True,
        )

        event = Event(
            id="e1",
            name="movie",
            description="d",
            duration="120",
            category="movie",
            is_blocked=False,
            artist_ids=[],
            artist_names=[],
        )

        self.mock_venue_repo.get_venue_by_id.return_value = venue
        self.mock_event_repo.get_by_id.return_value = event

        self.show_service.create_show(req)

        self.mock_show_repo.create_show.assert_called_once()
        args, kwargs = self.mock_show_repo.create_show.call_args
        show = kwargs["show"]

        assert show.venue_id == "v1"
        assert show.event_id == "e1"
        assert show.is_blocked is False

    def test_get_show_by_id_success(self):
        show = Show(
            id="s1",
            venue_id="v1",
            event_id="e1",
            is_blocked=False,
            price="300",
            show_date="2026-01-28",
            show_time="18:00",
            booked_seats=[],
        )

        venue = Venue(
            id="v1",
            name="PVR",
            city="delhi",
            state="delhi",
            host_id="host1",
            is_blocked=False,
            is_seat_layout_required=True,
        )

        self.mock_show_repo.get_show_by_id.return_value = show
        self.mock_venue_repo.get_venue_by_id.return_value = venue

        resp = self.show_service.get_show_by_id("s1")

        assert resp.id == "s1"
        assert resp.venue.venue_name == "PVR"

    def test_get_show_by_id_not_found(self):
        self.mock_show_repo.get_show_by_id.return_value = None

        with self.assertRaises(NotFoundException):
            self.show_service.get_show_by_id("missing")

    def test_get_show_by_id_blocked_show(self):
        show = MagicMock(is_blocked=True)

        self.mock_show_repo.get_show_by_id.return_value = show

        with self.assertRaises(NotFoundException):
            self.show_service.get_show_by_id("s1")

    def test_get_show_by_id_blocked_venue(self):
        show = Show(
            id="s1",
            venue_id="v1",
            event_id="e1",
            is_blocked=False,
            price="300",
            show_date="2026-01-28",
            show_time="18:00",
            booked_seats=[],
        )
        venue = MagicMock(is_blocked=True)

        self.mock_show_repo.get_show_by_id.return_value = show
        self.mock_venue_repo.get_venue_by_id.return_value = venue

        with self.assertRaises(NotFoundException):
            self.show_service.get_show_by_id("s1")

    def test_update_show_success(self):
        show = MagicMock(venue_id="v1")
        venue = MagicMock()

        self.mock_show_repo.get_show_by_id.return_value = show
        self.mock_venue_repo.get_venue_by_id.return_value = venue

        req = ShowUpdateReq(is_blocked=True)

        self.show_service.update_show("s1", req)

        self.mock_show_repo.update_show.assert_called_once_with(
            show_id="s1",
            is_blocked=True,
            venue=venue,
            show=show,
        )

    def test_update_show_not_found(self):
        self.mock_show_repo.get_show_by_id.return_value = None

        with self.assertRaises(NotFoundException):
            self.show_service.update_show("missing", ShowUpdateReq(is_blocked=True))

    # -------------------- get_event_shows --------------------

    def test_get_event_shows_customer_filters_blocked(self):
        shows = [
            Show("s1", "v1", "e1", False, "300", "2026-01-28", "18:00", []),
            Show("s2", "v1", "e1", True, "300", "2026-01-28", "18:00", []),
        ]

        venue = Venue(
            id="v1",
            name="PVR",
            city="delhi",
            state="delhi",
            host_id="host1",
            is_blocked=False,
            is_seat_layout_required=True,
        )

        self.mock_show_repo.list_by_event_city.return_value = shows
        self.mock_venue_repo.batch_get_venues.return_value = [venue]

        user = {"user_id": "u1", "role": Role.CUSTOMER.value}

        result = self.show_service.get_event_shows(
            event_id="e1",
            city="DELHI",
            user=user,
        )

        assert len(result) == 1
        assert result[0].id == "s1"
