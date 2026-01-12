import pytest

from app.services.venue_service import VenuService
from models.venue import Venue
from schemas.venues import VenueCreateReq
from custom_exceptions.generic import NotFoundException


class FakeVenueRepo:
    def __init__(self):
        self.by_id = {}
        self.update_calls = []
        self.delete_calls = []

    def add_venue(self, venue: Venue):
        self.by_id[str(venue.id)] = venue

    def get_venue_by_id(self, venue_id: str):
        return self.by_id.get(venue_id)

    def get_host_venues(self, host_id: str):
        return [v for v in self.by_id.values() if v.host_id == host_id]

    def update_venue(self, venue_id: str, host_id: str, is_blocked: bool):
        self.update_calls.append((venue_id, host_id, is_blocked))

    def delete_venue(self, venue_id: str, host_id: str):
        self.delete_calls.append((venue_id, host_id))


@pytest.fixture
def fake_repo():
    return FakeVenueRepo()


@pytest.fixture
def service(fake_repo):
    return VenuService(venue_repo=fake_repo)


def test_add_venue_lowercases_and_persists(service, fake_repo):
    req = VenueCreateReq(
        name="My Venue",
        city="Jaipur",
        state="Rajasthan",
        is_seat_layout_required=False,
    )

    venue = service.add_venue(req, host_id="host-1")

    assert venue.id is not None
    assert venue.name == "My Venue"
    assert venue.city == "jaipur"
    assert venue.state == "rajasthan"
    assert venue.host_id == "host-1"
    assert venue.is_blocked is False
    assert venue.is_seat_layout_required is False
    assert str(venue.id) in fake_repo.by_id


def test_get_venue_by_id_found(service, fake_repo):
    venue = Venue(
        id="v1",
        name="A",
        host_id="h1",
        city="c",
        state="s",
        is_blocked=False,
        is_seat_layout_required=True,
    )
    fake_repo.add_venue(venue)

    result = service.get_venue_by_id("v1")
    assert result is venue


def test_get_venue_by_id_missing_raises(service):
    with pytest.raises(NotFoundException):
        service.get_venue_by_id("missing")


def test_get_host_venues_all(service, fake_repo):
    v1 = Venue("v1", "A", "h1", "c", "s", False, True)
    v2 = Venue("v2", "B", "h1", "c", "s", True, False)
    v3 = Venue("v3", "C", "h2", "c", "s", False, True)
    for v in (v1, v2, v3):
        fake_repo.add_venue(v)

    venues = service.get_host_venues(host_id="h1")

    assert sorted(venues, key=lambda v: v.id) == sorted([v1, v2], key=lambda v: v.id)


def test_get_host_venues_blocked_only(service, fake_repo):
    v1 = Venue("v1", "A", "h1", "c", "s", False, True)
    v2 = Venue("v2", "B", "h1", "c", "s", True, False)
    for v in (v1, v2):
        fake_repo.add_venue(v)

    venues = service.get_host_venues(host_id="h1", is_blocked=True)

    assert venues == [v2]


def test_get_host_venues_unblocked_only(service, fake_repo):
    v1 = Venue("v1", "A", "h1", "c", "s", False, True)
    v2 = Venue("v2", "B", "h1", "c", "s", True, False)
    for v in (v1, v2):
        fake_repo.add_venue(v)

    venues = service.get_host_venues(host_id="h1", is_blocked=False)

    assert venues == [v1]


def test_update_venue_delegates(service, fake_repo):
    service.update_venue(venue_id="v1", host_id="h1", is_blocked=True)
    assert fake_repo.update_calls == [("v1", "h1", True)]


def test_delete_venue_delegates(service, fake_repo):
    service.delete_venue(venue_id="v1", host_id="h1")
    assert fake_repo.delete_calls == [("v1", "h1")]
