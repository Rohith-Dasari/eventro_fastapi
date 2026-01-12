import pytest

from app.services.show_service import ShowService
from models.shows import Show
from models.venue import Venue
from models.events import Event
from models.users import Role
from custom_exceptions.generic import NotFoundException


class FakeShowRepo:
    def __init__(self):
        self.created = []
        self.by_id = {}
        self.city_calls = []
        self.date_calls = []
        self.event_city_results = []
        self.event_date_results = []
        self.update_calls = []

    def create_show(self, show, venue, event):
        self.created.append((show, venue, event))

    def get_show_by_id(self, show_id):
        return self.by_id.get(show_id)

    def list_by_event_city(self, event_id, city):
        self.city_calls.append((event_id, city))
        return list(self.event_city_results)

    def list_by_event_date(self, event_id, city, date):
        self.date_calls.append((event_id, city, date))
        return list(self.event_date_results)

    def update_show(self, show_id, is_blocked, venue, show):
        self.update_calls.append((show_id, is_blocked, venue, show))


class FakeVenueRepo:
    def __init__(self):
        self.by_id = {}
        self.batched = []

    def get_venue_by_id(self, venue_id):
        return self.by_id.get(venue_id)

    def batch_get_venues(self, venue_ids):
        self.batched.append(list(venue_ids))
        return [self.by_id[v_id] for v_id in venue_ids if v_id in self.by_id]


class FakeEventRepo:
    def __init__(self, event=None):
        self.event = event

    def get_by_id(self, event_id):
        return self.event


@pytest.fixture
def event():
    return Event(
        id="e1",
        name="event",
        description="d",
        duration=60,
        category="movie",
        is_blocked=False,
        artist_ids=[],
        artist_names=[],
    )


@pytest.fixture
def repos(event):
    show_repo = FakeShowRepo()
    venue_repo = FakeVenueRepo()
    event_repo = FakeEventRepo(event=event)
    return show_repo, venue_repo, event_repo


@pytest.fixture
def service(repos):
    show_repo, venue_repo, event_repo = repos
    return ShowService(show_repo=show_repo, venue_repo=venue_repo, event_repo=event_repo)


def test_create_show_happy_path(service, repos, event):
    show_repo, venue_repo, _ = repos
    venue_repo.by_id["v1"] = Venue(
        id="v1",
        name="Venue",
        host_id="h1",
        city="jaipur",
        state="rj",
        is_blocked=False,
        is_seat_layout_required=False,
    )

    dto = type("ShowCreateReq", (), {
        "venue_id": "v1",
        "event_id": "e1",
        "price": 100,
        "show_date": "2024-01-01",
        "show_time": "19:00",
    })

    service.create_show(dto)

    assert len(show_repo.created) == 1
    created_show, created_venue, created_event = show_repo.created[0]
    assert created_show.event_id == "e1"
    assert created_show.venue_id == "v1"
    assert created_venue is venue_repo.by_id["v1"]
    assert created_event is event


def test_get_show_by_id_happy_path(service, repos):
    show_repo, venue_repo, _ = repos
    show = Show(
        id="s1",
        venue_id="v1",
        event_id="e1",
        is_blocked=False,
        price=100,
        show_date="2024-01-01",
        show_time="19:00",
        booked_seats=[],
    )
    venue = Venue(
        id="v1",
        name="Venue",
        host_id="h1",
        city="jaipur",
        state="rj",
        is_blocked=False,
        is_seat_layout_required=False,
    )
    show_repo.by_id["s1"] = show
    venue_repo.by_id["v1"] = venue

    resp = service.get_show_by_id("s1")

    assert resp.id == "s1"
    assert resp.venue.venue_id == "v1"
    assert resp.host_id == "h1"


def test_get_show_by_id_missing_raises(service):
    with pytest.raises(NotFoundException):
        service.get_show_by_id("missing")


def test_get_show_by_id_blocked_show_raises(service, repos):
    show_repo, venue_repo, _ = repos
    show = Show(
        id="s1",
        venue_id="v1",
        event_id="e1",
        is_blocked=True,
        price=100,
        show_date="2024-01-01",
        show_time="19:00",
        booked_seats=[],
    )
    show_repo.by_id["s1"] = show
    venue_repo.by_id["v1"] = Venue("v1", "Venue", "h1", "jaipur", "rj", False, False)

    with pytest.raises(NotFoundException):
        service.get_show_by_id("s1")


def test_get_show_by_id_blocked_venue_raises(service, repos):
    show_repo, venue_repo, _ = repos
    show = Show(
        id="s1",
        venue_id="v1",
        event_id="e1",
        is_blocked=False,
        price=100,
        show_date="2024-01-01",
        show_time="19:00",
        booked_seats=[],
    )
    venue = Venue("v1", "Venue", "h1", "jaipur", "rj", True, False)
    show_repo.by_id["s1"] = show
    venue_repo.by_id["v1"] = venue

    with pytest.raises(NotFoundException):
        service.get_show_by_id("s1")


def test_update_show_missing_show_raises(service):
    req = type("Req", (), {"is_blocked": True})
    with pytest.raises(NotFoundException):
        service.update_show("missing", req)


def test_update_show_missing_venue_raises(service, repos):
    show_repo, _, _ = repos
    show_repo.by_id["s1"] = Show("s1", "v1", "e1", False, 100, "2024-01-01", "19:00", [])
    req = type("Req", (), {"is_blocked": True})

    with pytest.raises(NotFoundException):
        service.update_show("s1", req)


def test_update_show_delegates(service, repos):
    show_repo, venue_repo, _ = repos
    show_repo.by_id["s1"] = Show("s1", "v1", "e1", False, 100, "2024-01-01", "19:00", [])
    venue_repo.by_id["v1"] = Venue("v1", "Venue", "h1", "jaipur", "rj", False, False)
    req = type("Req", (), {"is_blocked": True})

    service.update_show("s1", req)

    assert show_repo.update_calls == [("s1", True, venue_repo.by_id["v1"], show_repo.by_id["s1"])]


def test_get_event_shows_filters_blocked_for_customer(service, repos):
    show_repo, venue_repo, _ = repos
    show_blocked = Show("s1", "v1", "e1", True, 100, "2024-01-01", "19:00", [])
    show_ok = Show("s2", "v2", "e1", False, 100, "2024-01-01", "20:00", [])
    show_repo.event_city_results = [show_blocked, show_ok]
    venue_repo.by_id["v1"] = Venue("v1", "V1", "h1", "jaipur", "rj", False, False)
    venue_repo.by_id["v2"] = Venue("v2", "V2", "h2", "jaipur", "rj", False, False)

    user = {"role": Role.CUSTOMER.value}
    results = service.get_event_shows(event_id="e1", city="Jaipur", user=user)

    assert len(results) == 1
    assert results[0].id == "s2"


def test_get_event_shows_host_sees_only_own(service, repos):
    show_repo, venue_repo, _ = repos
    s1 = Show("s1", "v1", "e1", False, 100, "2024-01-01", "19:00", [])
    s2 = Show("s2", "v2", "e1", False, 100, "2024-01-01", "20:00", [])
    show_repo.event_city_results = [s1, s2]
    venue_repo.by_id["v1"] = Venue("v1", "V1", "h1", "jaipur", "rj", False, False)
    venue_repo.by_id["v2"] = Venue("v2", "V2", "h2", "jaipur", "rj", False, False)

    user = {"role": Role.HOST.value, "user_id": "h1"}
    results = service.get_event_shows(event_id="e1", city="Jaipur", user=user)

    assert [r.id for r in results] == ["s1"]


def test_get_event_shows_date_branch_and_city_lowercases(service, repos):
    show_repo, venue_repo, _ = repos
    s1 = Show("s1", "v1", "e1", False, 100, "2024-01-01", "19:00", [])
    show_repo.event_date_results = [s1]
    venue_repo.by_id["v1"] = Venue("v1", "V1", "h1", "jaipur", "rj", False, False)

    user = {"role": Role.CUSTOMER.value}
    results = service.get_event_shows(event_id="e1", city="JAIPUR", user=user, date="2024-01-01")

    assert [r.id for r in results] == ["s1"]
    assert show_repo.date_calls == [("e1", "jaipur", "2024-01-01")]


def test_get_event_shows_returns_empty_when_no_shows(service, repos):
    results = service.get_event_shows(event_id="e1", city="jaipur", user={"role": Role.CUSTOMER.value})
    assert results == []
