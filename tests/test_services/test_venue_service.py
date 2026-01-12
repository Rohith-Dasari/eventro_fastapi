import unittest
from unittest.mock import MagicMock

from app.services.venue_service import VenuService
from app.models.venue import Venue
from app.schemas.venues import VenueCreateReq
from app.custom_exceptions.generic import NotFoundException


class TestVenueService(unittest.TestCase):

    def setUp(self):
        self.mock_venue_repo = MagicMock()
        self.venue_service = VenuService(self.mock_venue_repo)

    def test_add_venue_success(self):
        req = VenueCreateReq(
            name="PVR",
            city="Delhi",
            state="Delhi",
            is_seat_layout_required=True,
        )

        venue = self.venue_service.add_venue(req, host_id="host1")

        assert venue.name == "PVR"
        assert venue.city == "delhi"
        assert venue.state == "delhi"
        assert venue.host_id == "host1"
        assert venue.is_blocked is False
        assert venue.id is not None

        self.mock_venue_repo.add_venue.assert_called_once()

    def test_get_venue_by_id_success(self):
        venue = Venue(
            id="v1",
            name="PVR",
            city="delhi",
            state="delhi",
            host_id="host1",
            is_blocked=False,
            is_seat_layout_required=True,
        )

        self.mock_venue_repo.get_venue_by_id.return_value = venue

        result = self.venue_service.get_venue_by_id("v1")

        assert result == venue
        self.mock_venue_repo.get_venue_by_id.assert_called_once_with("v1")

    def test_get_venue_by_id_not_found(self):
        self.mock_venue_repo.get_venue_by_id.return_value = None

        with self.assertRaises(NotFoundException):
            self.venue_service.get_venue_by_id("missing")

    def test_get_host_venues_no_filter(self):
        venues = [
            Venue("v1", "A", "delhi", "delhi", "host1", False, True),
            Venue("v2", "B", "delhi", "delhi", "host1", True, False),
        ]

        self.mock_venue_repo.get_host_venues.return_value = venues

        result = self.venue_service.get_host_venues("host1")

        assert result == venues

    def test_get_host_venues_is_blocked_true(self):
        venues = [
            Venue("v1", "A", "delhi", "delhi", "host1", False, True),
            Venue("v2", "B", "delhi", "delhi", "host1", True, False),
        ]

        self.mock_venue_repo.get_host_venues.return_value = venues

        result = self.venue_service.get_host_venues("host1", is_blocked=True)

        assert len(result) == 1
        assert result[0].is_blocked is True

    def test_get_host_venues_is_blocked_false(self):
        venues = [
            Venue("v1", "A", "delhi", "delhi", "host1", False, True),
            Venue("v2", "B", "delhi", "delhi", "host1", True, False),
        ]

        self.mock_venue_repo.get_host_venues.return_value = venues

        result = self.venue_service.get_host_venues("host1", is_blocked=False)

        assert len(result) == 1
        assert result[0].is_blocked is False

    def test_update_venue_calls_repo(self):
        self.venue_service.update_venue(
            venue_id="v1",
            host_id="host1",
            is_blocked=True,
        )

        self.mock_venue_repo.update_venue.assert_called_once_with("v1", "host1", True)

    def test_delete_venue_calls_repo(self):
        self.venue_service.delete_venue(
            venue_id="v1",
            host_id="host1",
        )

        self.mock_venue_repo.delete_venue.assert_called_once_with("v1", "host1")
