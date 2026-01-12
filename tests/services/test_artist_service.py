import pytest
from app.services.artist_service import ArtistService
from models.artists import Artist
from custom_exceptions.generic import NotFoundException

class FakeArtistRepo:
    def __init__(self):
        self.store = {}

    def get_by_id(self, artist_id):
        return self.store.get(artist_id)

    def batch_get_by_ids(self, artist_ids):
        return {aid: self.store[aid] for aid in artist_ids if aid in self.store}

    def add_artist(self, artist: Artist):
        self.store[artist.id] = artist
        return artist


@pytest.fixture
def fake_repo():
    return FakeArtistRepo()


@pytest.fixture
def service(fake_repo):
    return ArtistService(artist_repo=fake_repo)


def test_get_artist_by_id_success(service, fake_repo):
    a = Artist("id1", "Name1", "Bio1")
    fake_repo.store[a.id] = a

    result = service.get_artist_by_id("id1")
    assert result == a


def test_get_artist_by_id_not_found(service):
    with pytest.raises(NotFoundException):
        service.get_artist_by_id("nope")


def test_get_artists_batch_success(service, fake_repo):
    a1 = Artist("a1", "N1", "B1")
    a2 = Artist("a2", "N2", "B2")
    fake_repo.store[a1.id] = a1
    fake_repo.store[a2.id] = a2

    result = service.get_artists_batch(["a1", "a2"])
    assert result == [a1, a2]


def test_get_artists_batch_some_missing(service, fake_repo):
    a1 = Artist("a1", "N1", "B1")
    fake_repo.store[a1.id] = a1

    with pytest.raises(NotFoundException) as exc:
        service.get_artists_batch(["a1", "a2"])
    assert "a2" in exc.value.identifier  


def test_add_artist_creates_and_returns(service, fake_repo):
    artist = service.add_artist("NewName", "NewBio")

    assert isinstance(artist, Artist)
    assert artist.name == "NewName"
    assert artist.bio == "NewBio"
    assert fake_repo.store[artist.id] == artist
