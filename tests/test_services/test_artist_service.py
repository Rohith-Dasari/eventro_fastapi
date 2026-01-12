import unittest
from unittest.mock import MagicMock
from app.services.artist_service import ArtistService
from app.models.artists import Artist
from app.custom_exceptions.generic import NotFoundException


class TestArtistService(unittest.TestCase):

    def setUp(self):
        self.mock_artist_repo = MagicMock()
        self.artist_service = ArtistService(self.mock_artist_repo)

    def test_get_artist_by_id_success(self):
        artist = Artist(
            id="a1",
            name="Artist One",
            bio="bio",
        )
        self.mock_artist_repo.get_by_id.return_value = artist

        result = self.artist_service.get_artist_by_id("a1")

        assert result == artist
        self.mock_artist_repo.get_by_id.assert_called_once_with("a1")

    def test_get_artist_by_id_not_found(self):
        self.mock_artist_repo.get_by_id.return_value = None

        with self.assertRaises(NotFoundException) as ctx:
            self.artist_service.get_artist_by_id("missing")

        exc = ctx.exception
        assert exc.resource == "artist"
        assert exc.identifier == "missing"
        assert exc.status_code == 404

    def test_get_artists_batch_success(self):
        a1 = Artist("a1", "A1", "bio1")
        a2 = Artist("a2", "A2", "bio2")

        self.mock_artist_repo.batch_get_by_ids.return_value = {
            "a1": a1,
            "a2": a2,
        }

        result = self.artist_service.get_artists_batch(["a1", "a2"])

        assert result == [a1, a2]
        self.mock_artist_repo.batch_get_by_ids.assert_called_once_with(["a1", "a2"])

    def test_get_artists_batch_missing_ids(self):
        a1 = Artist("a1", "A1", "bio1")

        self.mock_artist_repo.batch_get_by_ids.return_value = {
            "a1": a1,
        }

        with self.assertRaises(NotFoundException) as ctx:
            self.artist_service.get_artists_batch(["a1", "a2"])

        exc = ctx.exception
        assert exc.resource == "artist"
        assert "a2" in exc.identifier
        assert exc.status_code == 404

    def test_get_artists_batch_preserves_order(self):
        a1 = Artist("a1", "A1", "bio1")
        a2 = Artist("a2", "A2", "bio2")

        self.mock_artist_repo.batch_get_by_ids.return_value = {
            "a2": a2,
            "a1": a1,
        }

        result = self.artist_service.get_artists_batch(["a1", "a2"])

        assert result == [a1, a2]

    def test_add_artist_creates_and_persists_artist(self):
        self.mock_artist_repo.add_artist.return_value = None

        artist = self.artist_service.add_artist(
            artist_name="New Artist",
            artist_bio="New Bio",
        )

        assert artist.name == "New Artist"
        assert artist.bio == "New Bio"
        assert artist.id is not None

        self.mock_artist_repo.add_artist.assert_called_once()
