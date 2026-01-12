import unittest
from unittest.mock import MagicMock

from app.services.event_service import EventService
from app.models.events import Event, Category
from app.models.users import Role
from app.custom_exceptions.generic import NotFoundException
from app.schemas.event import UpdateEventRequest


class TestEventService(unittest.TestCase):

    def setUp(self):
        self.mock_event_repo = MagicMock()
        self.mock_artist_service = MagicMock()
        self.event_service = EventService(
            event_repo=self.mock_event_repo,
            artist_service=self.mock_artist_service,
        )

    def test_create_event_success(self):
        artist1 = MagicMock(name="A1")
        artist1.name = "Artist1"
        artist2 = MagicMock(name="A2")
        artist2.name = "Artist2"

        self.mock_artist_service.get_artists_batch.return_value = [
            artist1,
            artist2,
        ]

        event = self.event_service.create_event(
            event_name="Rock Show",
            description="Live concert",
            duration="120",
            category=Category.MOVIE,
            artist_ids=["a1", "a2"],
        )

        assert event.name == "rock show"
        assert event.artist_names == ["Artist1", "Artist2"]
        assert event.is_blocked is False

        self.mock_artist_service.get_artists_batch.assert_called_once_with(["a1", "a2"])
        self.mock_event_repo.add_event.assert_called_once()

    def test_get_event_by_id_success_for_admin(self):
        event = Event(
            id="e1",
            name="event",
            description="d",
            duration="120",
            category="movie",
            is_blocked=True,
            artist_ids=[],
            artist_names=[],
        )
        self.mock_event_repo.get_by_id.return_value = event

        result = self.event_service.get_event_by_id(
            event_id="e1",
            user_role=Role.ADMIN.value,
        )

        assert result == event

    def test_get_event_by_id_blocked_for_customer(self):
        event = Event(
            id="e1",
            name="event",
            description="d",
            duration="120",
            category="movie",
            is_blocked=True,
            artist_ids=[],
            artist_names=[],
        )
        self.mock_event_repo.get_by_id.return_value = event

        with self.assertRaises(NotFoundException):
            self.event_service.get_event_by_id(
                event_id="e1",
                user_role=Role.CUSTOMER.value,
            )

    def test_get_event_by_id_not_found(self):
        self.mock_event_repo.get_by_id.return_value = None

        with self.assertRaises(NotFoundException):
            self.event_service.get_event_by_id(
                event_id="missing",
                user_role=Role.ADMIN.value,
            )

    def test_browse_events_by_city_customer_sees_only_unblocked(self):
        events = [
            Event("e1", "a", "d", "120", "movie", False, [], []),
            Event("e2", "b", "d", "120", "movie", True, [], []),
        ]
        self.mock_event_repo.get_events_by_city_and_name.return_value = events

        result = self.event_service.browse_events_by_city(
            city="delhi",
            user_role=Role.CUSTOMER.value,
        )

        assert len(result) == 1
        assert result[0].is_blocked is False

    def test_browse_events_by_city_admin_is_blocked_true(self):
        events = [
            Event("e1", "a", "d", "120", "movie", False, [], []),
            Event("e2", "b", "d", "120", "movie", True, [], []),
        ]
        self.mock_event_repo.get_events_by_city_and_name.return_value = events

        result = self.event_service.browse_events_by_city(
            city="delhi",
            is_blocked=True,
            user_role=Role.ADMIN.value,
        )

        assert len(result) == 1
        assert result[0].is_blocked is True

    def test_browse_events_by_name_customer_with_city(self):
        events = [
            Event("e1", "rock", "d", "120", "movie", False, [], []),
        ]
        self.mock_event_repo.get_events_by_city_and_name.return_value = events

        result = self.event_service.browse_events_by_name(
            user_role=Role.CUSTOMER.value,
            event_name="rock",
            city="delhi",
        )

        assert result == events

    def test_browse_events_by_name_non_customer(self):
        events = [
            Event("e1", "rock", "d", "120", "movie", False, [], []),
        ]
        self.mock_event_repo.get_events_by_name.return_value = events

        result = self.event_service.browse_events_by_name(
            user_role=Role.ADMIN.value,
            event_name="rock",
        )

        assert result == events

    def test_browse_events_by_name_filters_blocked_for_non_admin(self):
        events = [
            Event("e1", "rock", "d", "120", "movie", False, [], []),
            Event("e2", "rock", "d", "120", "movie", True, [], []),
        ]
        self.mock_event_repo.get_events_by_name.return_value = events

        result = self.event_service.browse_events_by_name(
            user_role=Role.CUSTOMER.value,
            event_name="rock",
        )

        assert len(result) == 1
        assert result[0].is_blocked is False

    def test_get_host_events_calls_repo(self):
        events = [
            Event("e1", "a", "d", "120", "movie", False, [], []),
        ]
        self.mock_event_repo.get_events_of_host.return_value = events

        result = self.event_service.get_host_events("host1")

        assert result == events
        self.mock_event_repo.get_events_of_host.assert_called_once_with(host_id="host1")

    def test_update_event_calls_repo(self):
        req = UpdateEventRequest(is_blocked=True)

        self.event_service.update_event("e1", req)

        self.mock_event_repo.update_event.assert_called_once_with(
            event_id="e1",
            is_blocked=True,
        )
