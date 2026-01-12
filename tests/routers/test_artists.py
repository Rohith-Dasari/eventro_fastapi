import pytest
from app.main import app
import dependencies as deps

from tests.conftest import (
    FakeArtistService,
    NoArtistService,
    fake_current_user_admin,
    fake_current_user_customer,
)

def test_get_artist_exists_returns_data(client):
    app.dependency_overrides[deps.get_artist_service] = lambda: FakeArtistService()

    res = client.get("/artists/a1")
    assert res.status_code == 200

    body = res.json()
    assert body["status_code"] == 200
    assert body["data"]["id"] == "a1"
    assert body["data"]["name"] == "Alice"


def test_get_artist_not_exists_returns_404(client):
    app.dependency_overrides[deps.get_artist_service] = lambda: NoArtistService()

    res = client.get("/artists/nonexistent")
    assert res.status_code == 404

    body = res.json()
    assert body["status_code"] == 404
    assert "not found" in body["message"].lower()
def test_add_artist_happy_path_creates_artist(client):
    app.dependency_overrides[deps.get_artist_service] = lambda: FakeArtistService()
    app.dependency_overrides[deps.get_current_user] = fake_current_user_admin

    payload = {"name": "New Artist", "bio": "Nice bio"}
    res = client.post("/artists", json=payload)

    assert res.status_code == 200
    body = res.json()

    assert body["status_code"] == 201
    assert body["data"]["name"] == payload["name"]
    assert body["data"]["bio"] == payload["bio"]


def test_add_artist_customer_role_forbidden(client):
    app.dependency_overrides[deps.get_artist_service] = lambda: FakeArtistService()
    app.dependency_overrides[deps.get_current_user] = fake_current_user_customer

    payload = {"name": "Forbidden Artist", "bio": "No perms"}
    res = client.post("/artists", json=payload)

    assert res.status_code == 403
    body = res.json()

    assert body["status_code"] == 403
    assert "unauthorised" in body["message"].lower()


def test_add_artist_invalid_data_returns_422(client):
    app.dependency_overrides[deps.get_artist_service] = lambda: FakeArtistService()
    app.dependency_overrides[deps.get_current_user] = fake_current_user_admin

    payload = {"bio": "Missing name"}
    res = client.post("/artists", json=payload)

    assert res.status_code == 422

    body = res.json()
    assert body["status_code"] == 422
