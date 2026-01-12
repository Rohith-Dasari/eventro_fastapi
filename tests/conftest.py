import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app.main import app
import dependencies as deps
from custom_exceptions.generic import NotFoundException


class FakeArtistService:
    def __init__(self):
        self.artists = {
            "a1": {"id": "a1", "name": "Alice", "bio": "Bio"}
        }

    def get_artist_by_id(self, artist_id: str):
        return self.artists.get(artist_id)

    def add_artist(self, name: str, bio: str):
        new = {"id": "new-id", "name": name, "bio": bio}
        self.artists[new["id"]] = new
        return new


class NoArtistService:
    def get_artist_by_id(self, artist_id: str):
        raise NotFoundException(resource="artist", identifier=artist_id, status_code=404)

    def add_artist(self, name: str, bio: str):
        return None


class FakeUserService:
    def __init__(self, signup_token="signup-token", login_token="login-token"):
        self.signup_calls = []
        self.login_calls = []
        self.signup_token = signup_token
        self.login_token = login_token
        self.signup_exception = None
        self.login_exception = None

    def signup(self, email: str, username: str, password: str, phone: str):
        self.signup_calls.append((email, username, password, phone))
        if self.signup_exception:
            raise self.signup_exception
        return self.signup_token

    def login(self, email: str, password: str):
        self.login_calls.append((email, password))
        if self.login_exception:
            raise self.login_exception
        return self.login_token


class FakeUsersRouterUserService:
    def __init__(self):
        self.profile_calls = []

    def get_user_profile(self, user_id: str):
        self.profile_calls.append(user_id)
        return {"id": user_id, "username": "alice"}


class FakeBookingService:
    def __init__(self):
        self.booking_calls = []
        self.create_calls = []
        self.create_exception = None

    def get_user_bookings(self, user_id: str):
        self.booking_calls.append(user_id)
        return [
            {"booking_id": "b1", "user_id": user_id},
            {"booking_id": "b2", "user_id": user_id},
        ]

    def create_booking(self, req, user_id: str):
        self.create_calls.append((req, user_id))
        if self.create_exception:
            raise self.create_exception
        return {"id": "bk1"}


class FakeVenueService:
    def __init__(self):
        self.host_calls = []
        self.return_value = [{"id": "v1"}]
        self.add_calls = []
        self.get_calls = []
        self.update_calls = []
        self.delete_calls = []
        self.venue_return = {"id": "v-obj"}
        self.not_found_ids = set()
        self.client_error_ids = set()

    def get_host_venues(self, host_id: str, is_blocked=None):
        self.host_calls.append((host_id, is_blocked))
        return list(self.return_value)

    def add_venue(self, req, host_id):
        self.add_calls.append((req, host_id))
        return self.venue_return

    def get_venue_by_id(self, venue_id: str):
        self.get_calls.append(venue_id)
        if venue_id in self.not_found_ids:
            raise NotFoundException(resource="venue", identifier=venue_id, status_code=404)
        return self.venue_return

    def update_venue(self, venue_id: str, host_id: str, is_blocked: bool):
        if venue_id in self.not_found_ids:
            raise NotFoundException(resource="venue", identifier=venue_id, status_code=404)
        if venue_id in self.client_error_ids:
            raise ClientError({"Error": {"Code": "500", "Message": "update failed"}}, "UpdateVenue")
        self.update_calls.append((venue_id, host_id, is_blocked))

    def delete_venue(self, venue_id: str, host_id: str):
        if venue_id in self.not_found_ids:
            raise NotFoundException(resource="venue", identifier=venue_id, status_code=404)
        if venue_id in self.client_error_ids:
            raise ClientError({"Error": {"Code": "500", "Message": "delete failed"}}, "DeleteVenue")
        self.delete_calls.append((venue_id, host_id))


class FakeEventService:
    def __init__(self):
        self.host_calls = []
        self.return_value = [{"id": "e1"}]
        self.create_calls = []
        self.get_calls = []
        self.browse_city_calls = []
        self.browse_name_calls = []
        self.update_calls = []

    def create_event(self, event_name, description, duration, category, artist_ids):
        cat_val = category.value if hasattr(category, "value") else category
        self.create_calls.append((event_name, description, duration, cat_val, artist_ids))
        return {"id": "e-created"}

    def get_event_by_id(self, event_id, user_role):
        self.get_calls.append((event_id, user_role))
        if hasattr(self, "not_found_ids") and event_id in getattr(self, "not_found_ids"):
            raise NotFoundException("event", event_id, status_code=404)
        return {"id": event_id, "blocked": False}

    def browse_events_by_city(self, city, is_blocked, user_role):
        self.browse_city_calls.append((city, is_blocked, user_role))
        return [{"id": "e-city"}]

    def browse_events_by_name(self, event_name, city, user_role):
        self.browse_name_calls.append((event_name, city, user_role))
        return [{"id": "e-name"}]

    def update_event(self, event_id, update_req):
        self.update_calls.append((event_id, update_req))
        return None

    def get_host_events(self, host_id: str):
        self.host_calls.append(host_id)
        return list(self.return_value)


class FakeShowService:
    def __init__(self):
        self.create_calls = []
        self.get_calls = []
        self.list_calls = []
        self.update_calls = []
        self.not_found_ids = set()

    def create_show(self, show_dto):
        self.create_calls.append(show_dto)

    def get_show_by_id(self, show_id: str):
        self.get_calls.append(show_id)
        if show_id in self.not_found_ids:
            raise NotFoundException("show", show_id, 404)
        return {"id": show_id}

    def get_event_shows(self, event_id: str, city: str, user, date=None):
        self.list_calls.append((event_id, city, user, date))
        return [{"id": "s1"}]

    def update_show(self, show_id: str, req):
        if show_id in self.not_found_ids:
            raise NotFoundException("show", show_id, 404)
        self.update_calls.append((show_id, req))
        return None


def override_require_roles(user):
    def factory(_roles):
        return lambda: user

    return factory


def fake_current_user_admin():
    return {"user_id": "u1", "role": "admin"}


def fake_current_user_customer():
    return {"user_id": "u2", "role": "customer"}


@asynccontextmanager
async def noop_lifespan(_app):
    yield



@pytest.fixture
def client():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides[deps.get_artist_service] = lambda: FakeArtistService()
    app.dependency_overrides[deps.get_current_user] = fake_current_user_admin
    app.state.artist_service = FakeArtistService()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides = {}


@pytest.fixture
def auth_client():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    fake_user_service = FakeUserService()
    app.dependency_overrides[deps.get_user_service] = lambda: fake_user_service

    with TestClient(app) as client:
        yield client, fake_user_service

    app.dependency_overrides = {}


@pytest.fixture
def users_client():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    fake_user_service = FakeUsersRouterUserService()
    fake_booking_service = FakeBookingService()
    app.dependency_overrides[deps.get_current_user] = fake_current_user_customer
    app.dependency_overrides[deps.get_user_service] = lambda: fake_user_service
    app.dependency_overrides[deps.get_booking_service] = lambda: fake_booking_service

    with TestClient(app) as client:
        yield client, fake_user_service, fake_booking_service

    app.dependency_overrides = {}


@pytest.fixture
def hosts_client_admin():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    venue_svc = FakeVenueService()
    event_svc = FakeEventService()
    user = {"user_id": "admin-id", "role": "admin"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_venue_service] = lambda: venue_svc
    app.dependency_overrides[deps.get_event_service] = lambda: event_svc

    with TestClient(app) as client:
        yield client, venue_svc, event_svc

    app.dependency_overrides = {}


@pytest.fixture
def hosts_client_host_mismatch():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    venue_svc = FakeVenueService()
    event_svc = FakeEventService()
    user = {"user_id": "h-other", "role": "host"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_venue_service] = lambda: venue_svc
    app.dependency_overrides[deps.get_event_service] = lambda: event_svc

    with TestClient(app) as client:
        yield client, venue_svc, event_svc

    app.dependency_overrides = {}


@pytest.fixture
def venues_client_admin():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    venue_svc = FakeVenueService()
    user = {"user_id": "admin-id", "role": "admin"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.require_roles] = override_require_roles(user)
    app.dependency_overrides[deps.get_venue_service] = lambda: venue_svc

    with TestClient(app) as client:
        yield client, venue_svc, user

    app.dependency_overrides = {}


@pytest.fixture
def venues_client_host():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    venue_svc = FakeVenueService()
    user = {"user_id": "h1", "role": "host"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.require_roles] = override_require_roles(user)
    app.dependency_overrides[deps.get_venue_service] = lambda: venue_svc

    with TestClient(app) as client:
        yield client, venue_svc, user

    app.dependency_overrides = {}


@pytest.fixture
def events_client_admin():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    event_svc = FakeEventService()
    user = {"user_id": "admin-id", "role": "admin"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.require_roles] = override_require_roles(user)
    app.dependency_overrides[deps.get_event_service] = lambda: event_svc

    with TestClient(app) as client:
        yield client, event_svc, user

    app.dependency_overrides = {}


@pytest.fixture
def events_client_customer():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    event_svc = FakeEventService()
    user = {"user_id": "u2", "role": "customer"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.require_roles] = override_require_roles(user)
    app.dependency_overrides[deps.get_event_service] = lambda: event_svc

    with TestClient(app) as client:
        yield client, event_svc, user

    app.dependency_overrides = {}


@pytest.fixture
def events_client_customer_forbidden():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    event_svc = FakeEventService()
    user = {"user_id": "u2", "role": "customer"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_event_service] = lambda: event_svc

    with TestClient(app) as client:
        yield client, event_svc, user

    app.dependency_overrides = {}


@pytest.fixture
def shows_client_host():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    show_svc = FakeShowService()
    user = {"user_id": "h1", "role": "host"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.require_roles] = override_require_roles(user)
    app.dependency_overrides[deps.get_show_service] = lambda: show_svc

    with TestClient(app) as client:
        yield client, show_svc, user

    app.dependency_overrides = {}


@pytest.fixture
def shows_client_customer():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    show_svc = FakeShowService()
    user = {"user_id": "u2", "role": "customer"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_show_service] = lambda: show_svc

    with TestClient(app) as client:
        yield client, show_svc, user

    app.dependency_overrides = {}


@pytest.fixture
def bookings_client_customer():
    app.dependency_overrides = {}
    app.router.lifespan_context = noop_lifespan
    booking_svc = FakeBookingService()
    user = {"user_id": "u2", "role": "customer"}
    app.dependency_overrides[deps.get_current_user] = lambda: user
    app.dependency_overrides[deps.get_booking_service] = lambda: booking_svc

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, booking_svc, user

    app.dependency_overrides = {}


__all__ = [
    "FakeArtistService",
    "NoArtistService",
    "FakeUserService",
    "FakeUsersRouterUserService",
    "FakeBookingService",
    "FakeVenueService",
    "FakeEventService",
    "override_require_roles",
    "fake_current_user_admin",
    "fake_current_user_customer",
    "client",
    "auth_client",
    "users_client",
    "hosts_client_admin",
    "hosts_client_host_mismatch",
    "venues_client_admin",
    "venues_client_host",
    "events_client_admin",
    "events_client_customer",
    "events_client_customer_forbidden",
    "shows_client_host",
    "shows_client_customer",
    "bookings_client_customer",
]
