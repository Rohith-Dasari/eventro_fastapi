import pytest

from app.services.event_service import EventService
from models.events import Event, Category
from models.artists import Artist
from models.users import Role
from custom_exceptions.generic import NotFoundException


class FakeArtistService:
    def __init__(self, artists_by_id=None, should_raise=False):
        self.artists_by_id = artists_by_id or {}
        self.should_raise = should_raise

    def get_artists_batch(self, artist_ids):
        if self.should_raise:
            raise NotFoundException("artist", ",".join(artist_ids), status_code=404)
        return [self.artists_by_id[aid] for aid in artist_ids if aid in self.artists_by_id]


class FakeEventRepo:
    def __init__(self):
        self.added = []
        self.by_id = {}
        self.city_name_results = []
        self.name_results = []
        self.host_results = []
        self.update_calls = []
        self.city_calls = []
        self.name_calls = []

    def add_event(self, event: Event):
        self.added.append(event)
        self.by_id[event.id] = event

    def get_by_id(self, event_id: str):
        return self.by_id.get(event_id)

    def get_events_by_city_and_name(self, city: str, name: str = ""):
        self.city_calls.append((city, name))
        return list(self.city_name_results)

    def get_events_by_name(self, name: str):
        self.name_calls.append(name)
        return list(self.name_results)

    def get_events_of_host(self, host_id: str):
        return list(self.host_results)

    def update_event(self, event_id: str, is_blocked: bool):
        self.update_calls.append((event_id, is_blocked))


@pytest.fixture
def repo():
    return FakeEventRepo()


@pytest.fixture
def artist_service():
    artists = {
        "a1": Artist(id="a1", name="Alice", bio=None),
        "a2": Artist(id="a2", name="Bob", bio=None),
    }
    return FakeArtistService(artists_by_id=artists)


@pytest.fixture
def service(repo, artist_service):
    return EventService(event_repo=repo, artist_service=artist_service)


def test_create_event_happy_path(service, repo):
    event = service.create_event(
        event_name="RockShow",
        description="Desc",
        duration="120",
        category=Category.PARTY,
        artist_ids=["a1", "a2"],
    )

    assert event.name == "rockshow"  # lowercased
    assert event.category == "party"
    assert event.artist_names == ["Alice", "Bob"]
    assert repo.added and repo.added[0] is event


def test_create_event_missing_artist_raises(repo):
    service = EventService(event_repo=repo, artist_service=FakeArtistService(should_raise=True))
    with pytest.raises(NotFoundException):
        service.create_event(
            event_name="Show",
            description="Desc",
            duration="120",
            category=Category.MOVIE,
            artist_ids=["missing"],
        )


def test_get_event_by_id_found_unblocked(service, repo):
    e = Event(id="e1", name="n", description="d", duration=60, category="movie", is_blocked=False, artist_ids=[], artist_names=[])
    repo.by_id[e.id] = e

    result = service.get_event_by_id(event_id="e1", user_role=Role.CUSTOMER.value)
    assert result is e


def test_get_event_by_id_blocked_non_admin_raises(service, repo):
    e = Event(id="e1", name="n", description="d", duration=60, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.by_id[e.id] = e

    with pytest.raises(NotFoundException):
        service.get_event_by_id(event_id="e1", user_role=Role.CUSTOMER.value)


def test_get_event_by_id_blocked_admin_allowed(service, repo):
    e = Event(id="e1", name="n", description="d", duration=60, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.by_id[e.id] = e

    result = service.get_event_by_id(event_id="e1", user_role=Role.ADMIN.value)
    assert result is e


def test_browse_events_by_city_filters_blocked_for_customers(service, repo):
    e1 = Event(id="e1", name="a", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])
    e2 = Event(id="e2", name="b", description="d", duration=10, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.city_name_results = [e1, e2]

    events = service.browse_events_by_city(user_role=Role.CUSTOMER.value, city="jaipur")

    assert events == [e1]
    assert repo.city_calls == [("jaipur", "")]


def test_browse_events_by_city_admin_is_blocked_true_returns_only_blocked(service, repo):
    e1 = Event(id="e1", name="a", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])
    e2 = Event(id="e2", name="b", description="d", duration=10, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.city_name_results = [e1, e2]

    events = service.browse_events_by_city(user_role=Role.ADMIN.value, city="jaipur", is_blocked=True)

    assert events == [e2]
    assert repo.city_calls == [("jaipur", "")]


def test_browse_events_by_city_admin_default_returns_all(service, repo):
    e1 = Event(id="e1", name="a", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])
    e2 = Event(id="e2", name="b", description="d", duration=10, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.city_name_results = [e1, e2]

    events = service.browse_events_by_city(user_role=Role.ADMIN.value, city="jaipur", is_blocked=None)

    assert events == [e1, e2]
    assert repo.city_calls == [("jaipur", "")]


def test_browse_events_by_name_customer_city_uses_city_and_filters_blocked(service, repo):
    e1 = Event(id="e1", name="a", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])
    e2 = Event(id="e2", name="b", description="d", duration=10, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.city_name_results = [e1, e2]
    repo.name_results = [Event(id="x", name="n", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])]

    events = service.browse_events_by_name(user_role=Role.CUSTOMER.value, event_name="concert", city="NYC")

    assert events == [e1]
    assert repo.city_calls == [("NYC", "concert")]
    assert repo.name_calls == []


def test_browse_events_by_name_customer_no_city_uses_name_and_filters(service, repo):
    e1 = Event(id="e1", name="a", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])
    e2 = Event(id="e2", name="b", description="d", duration=10, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.name_results = [e1, e2]

    events = service.browse_events_by_name(user_role=Role.CUSTOMER.value, event_name="concert", city=None)

    assert events == [e1]
    assert repo.name_calls == ["concert"]
    assert repo.city_calls == []


def test_browse_events_by_name_admin_returns_all_and_uses_name_lookup(service, repo):
    e1 = Event(id="e1", name="a", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])
    e2 = Event(id="e2", name="b", description="d", duration=10, category="movie", is_blocked=True, artist_ids=[], artist_names=[])
    repo.name_results = [e1, e2]

    events = service.browse_events_by_name(user_role=Role.ADMIN.value, event_name="concert", city="NYC")

    assert events == [e1, e2]
    assert repo.name_calls == ["concert"]
    assert repo.city_calls == []


def test_get_host_events(service, repo):
    repo.host_results = [Event(id="e1", name="n", description="d", duration=10, category="movie", is_blocked=False, artist_ids=[], artist_names=[])]

    events = service.get_host_events(host_id="h1")

    assert events == repo.host_results


def test_update_event_delegates(service, repo):
    service.update_event(event_id="e1", update_req=type("Req", (), {"is_blocked": True}))
    assert repo.update_calls == [("e1", True)]
