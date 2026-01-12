import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_artist_service
from unittest.mock import MagicMock
from app.models.artists import Artist
from app.dependencies import get_current_user
from app.custom_exceptions.generic import NotFoundException


class TestArtistRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_artist_service = MagicMock()
        app.dependency_overrides[get_artist_service] = lambda: self.mock_artist_service
        self.mock_get_current_user = MagicMock()
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "admin",
        }

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_get_artist_exists_returns_data(self):
        artist = Artist(id="1", name="sample", bio="bio")
        self.mock_artist_service.get_artist_by_id.return_value = artist

        res = self.client.get("/artists/a1")
        assert res.status_code == 200

        body = res.json()
        assert body["status_code"] == 200
        assert body["data"]["id"] == "1"
        assert body["data"]["name"] == "sample"

    def test_get_artist_not_exists_returns_404(self):
        self.mock_artist_service.get_artist_by_id.side_effect = NotFoundException(
            "artist", "nonexistent", 404
        )

        res = self.client.get("/artists/nonexistent")
        assert res.status_code == 404

        body = res.json()
        assert body["status_code"] == 404

    def test_add_artist_happy_path_creates_artist(self):
        artist = Artist(id="1", name="New Artist", bio="Nice bio")
        self.mock_artist_service.add_artist.return_value = artist

        payload = {"name": "New Artist", "bio": "Nice bio"}
        res = self.client.post("/artists", json=payload)

        assert res.status_code == 200
        body = res.json()

        assert body["status_code"] == 201
        assert body["data"]["name"] == payload["name"]
        assert body["data"]["bio"] == payload["bio"]

    def test_add_artist_customer_role_forbidden(self):
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": "u1",
            "role": "customer",
        }

        payload = {"name": "Forbidden Artist", "bio": "No perms"}
        res = self.client.post("/artists", json=payload)

        assert res.status_code == 403
        body = res.json()

        assert body["status_code"] == 403
        assert "unauthorised" in body["message"].lower()

    def test_add_artist_invalid_data_returns_422(self):

        payload = {"bio": "Missing name"}
        res = self.client.post("/artists", json=payload)

        assert res.status_code == 422

        body = res.json()
        assert body["status_code"] == 422
