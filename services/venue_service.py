from repository.venue_repository import VenueRepository
from models.venue import Venue
from schemas.venues import VenueCreateReq
from uuid import uuid4
from typing import List


class VenuService:
    def __init__(self, venue_repo: VenueRepository):
        self.venue_repo = venue_repo

    def add_venue(self, venue: VenueCreateReq, host_id: str) -> Venue:
        venue = Venue(
            id=uuid4(),
            name=venue.name,
            city=venue.city,
            host_id=host_id,
            state=venue.state,
            is_blocked=False,
            is_seat_layout_required=venue.is_seat_layout_required,
        )

        self.venue_repo.add_venue(venue=venue)
        return venue

    def get_venue_by_id(self, venue_id: str) -> Venue:
        venue = self.venue_repo.get_venue_by_id(venue_id)
        return venue

    def get_host_venues(self, host_id: str) -> List[Venue]:
        venues = self.venue_repo.get_host_venues(host_id=host_id)
        return venues

    def update_venue(self, venue_id: str, host_id: str, is_blocked: bool):
        self.venue_repo.update_venue(venue_id, host_id, is_blocked)

    def delete_venue(self, venue_id: str, host_id: str):
        self.venue_repo.delete_venue(venue_id, host_id)
