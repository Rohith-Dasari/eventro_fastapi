from unittest.mock import MagicMock
import pytest

from app.repository.artist_repository import ArtistRepository
from app.models.artists import Artist


def make_table_mock():
    table = MagicMock()
    table.name = "artists"
    table.meta.client = MagicMock()
    return table


def test_get_by_id_found():
    table = make_table_mock()
    table.get_item.return_value = {
        "Item": {"pk": "ARTIST#a1", "sk": "DETAILS", "name": "Alice", "bio": "Bio"}
    }
    repo = ArtistRepository(table=table)

    artist = repo.get_by_id("a1")

    assert isinstance(artist, Artist)
    assert artist.id == "a1"
    assert artist.name == "Alice"
    assert artist.bio == "Bio"
    table.get_item.assert_called_once_with(Key={"pk": "ARTIST#a1", "sk": "DETAILS"})


def test_get_by_id_missing_returns_none():
    table = make_table_mock()
    table.get_item.return_value = {}
    repo = ArtistRepository(table=table)

    artist = repo.get_by_id("missing")

    assert artist is None
    table.get_item.assert_called_once_with(
        Key={"pk": "ARTIST#missing", "sk": "DETAILS"}
    )


def test_batch_get_by_ids_returns_map():
    table = make_table_mock()
    table.meta.client.batch_get_item.return_value = {
        "Responses": {
            table.name: [
                {"pk": "ARTIST#a1", "sk": "DETAILS", "name": "A1", "bio": "B1"},
                {"pk": "ARTIST#a2", "sk": "DETAILS", "name": "A2", "bio": "B2"},
            ]
        }
    }
    repo = ArtistRepository(table=table)

    result = repo.batch_get_by_ids(["a1", "a2", "missing"])

    assert set(result.keys()) == {"a1", "a2"}
    assert result["a1"].name == "A1"
    assert result["a2"].bio == "B2"
    expected_keys = [
        {"pk": "ARTIST#a1", "sk": "DETAILS"},
        {"pk": "ARTIST#a2", "sk": "DETAILS"},
        {"pk": "ARTIST#missing", "sk": "DETAILS"},
    ]
    table.meta.client.batch_get_item.assert_called_once_with(
        RequestItems={table.name: {"Keys": expected_keys}}
    )


def test_add_artist_calls_put_item():
    table = make_table_mock()
    repo = ArtistRepository(table=table)
    artist = Artist(id="a1", name="Alice", bio="Bio")

    returned = repo.add_artist(artist)

    assert returned is artist
    table.put_item.assert_called_once_with(
        Item={
            "pk": "ARTIST#a1",
            "sk": "DETAILS",
            "name": "Alice",
            "bio": "Bio",
        }
    )
