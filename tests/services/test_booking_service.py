import pytest

from app.services.booking_service import BookingService
from models.shows import Show
from models.events import Event
from models.venue import Venue
from models.booking import Booking
from schemas.booking import BookingReq, BookingResponse


class FakeBookingRepo:
    def __init__(self):
        self.added = []
        self.bookings = {}

    def add_booking(self, venue, event, show, booking):
        self.added.append((venue, event, show, booking))
        self.bookings.setdefault(booking.user_id, []).append(booking)

    def get_bookings(self, user_id):
        return self.bookings.get(user_id, [])


class FakeShowRepo:
    def __init__(self, show):
        self.show = show

    def get_show_by_id(self, show_id):
        return self.show


class FakeEventRepo:
    def __init__(self, event):
        self.event = event

    def get_by_id(self, event_id):
        return self.event


class FakeVenueRepo:
    def __init__(self, venue):
        self.venue = venue

    def get_venue_by_id(self, venue_id):
        return self.venue


@pytest.fixture
def base_entities():
    show = Show(
        id="s1",
        venue_id="v1",
        event_id="e1",
        is_blocked=False,
        price=150,
        show_date="2024-01-01",
        show_time="19:00",
        booked_seats=["A1"],
    )
    event = Event(
        id="e1",
        name="Concert",
        description="Desc",
        duration=120,
        category="concert",
        is_blocked=False,
        artist_ids=[],
        artist_names=[],
    )
    venue = Venue(
        id="v1",
        name="Main Hall",
        host_id="h1",
        city="jaipur",
        state="rj",
        is_blocked=False,
        is_seat_layout_required=False,
    )
    return show, event, venue


@pytest.fixture
def service(base_entities):
    show, event, venue = base_entities
    booking_repo = FakeBookingRepo()
    show_repo = FakeShowRepo(show)
    event_repo = FakeEventRepo(event)
    venue_repo = FakeVenueRepo(venue)
    svc = BookingService(
        booking_repo=booking_repo,
        show_repo=show_repo,
        event_repo=event_repo,
        venue_repo=venue_repo,
    )
    return svc, booking_repo, show_repo, event_repo, venue_repo


def test_create_booking_happy_path(service, base_entities):
    svc, booking_repo, _, _, _ = service
    req = BookingReq(show_id="s1", seats=["A2", "A3"])

    resp = svc.create_booking(req=req, user_id="u1")

    assert isinstance(resp, BookingResponse)
    assert resp.total_price == 2 * base_entities[0].price
    assert resp.booking_id
    assert booking_repo.added  # repo was called
    venue, event, show, booking = booking_repo.added[0]
    assert booking.user_id == "u1"
    assert venue.id == "v1"
    assert event.id == "e1"
    assert show.id == "s1"
    assert set(booking.seats) == {"A2", "A3"}


def test_create_booking_rejects_conflicting_seats(service):
    svc, _, _, _, _ = service
    req = BookingReq(show_id="s1", seats=["A1", "A2"])  # A1 already booked

    with pytest.raises(Exception):
        svc.create_booking(req=req, user_id="u1")


def test_get_user_bookings_returns_repo_list(service, base_entities):
    svc, booking_repo, *_ = service
    req = BookingReq(show_id="s1", seats=["A2"])
    svc.create_booking(req=req, user_id="u1")

    bookings = svc.get_user_bookings(user_id="u1")

    assert bookings and isinstance(bookings[0], Booking)


def test_create_booking_uses_total_price(service, base_entities):
    svc, _, _, _, _ = service
    req = BookingReq(show_id="s1", seats=["A2", "A3", "A4"])

    resp = svc.create_booking(req=req, user_id="u1")

    assert resp.total_price == 3 * base_entities[0].price
