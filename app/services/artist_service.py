from app.repository.artist_repository import ArtistRepository
from app.models.artists import Artist
from typing import Optional, List
from app.custom_exceptions.generic import NotFoundException
import uuid


class ArtistService:
    def __init__(self, artist_repo: ArtistRepository):
        self.artist_repo = artist_repo

    def get_artist_by_id(self, artist_id: str) -> Artist:
        artist = self.artist_repo.get_by_id(artist_id)
        if not artist:
            raise NotFoundException(resource="artist", identifier=artist_id, status_code=404)
        return artist

    def get_artists_batch(self, artist_ids: List[str]) -> List[Artist]:

        artists_map = self.artist_repo.batch_get_by_ids(artist_ids)

        missing = set(artist_ids) - set(artists_map.keys())
        if missing:
            raise NotFoundException(resource="artist", identifier=", ".join(missing), status_code=404)

        return [artists_map[aid] for aid in artist_ids]

    def add_artist(self, artist_name: str, artist_bio: str):
        artist = Artist(str(uuid.uuid4()), artist_name, artist_bio)
        self.artist_repo.add_artist(artist)
        return artist
