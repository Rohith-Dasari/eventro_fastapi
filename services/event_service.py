from services.artist_service import ArtistService
from repository.event_repository import EventRepository
from models.events import Category, Event
from custom_exceptions.event_exceptions import EventNotFound
import uuid
from typing import List
from schemas.event import UpdateEventRequest


class EventService:
    def __init__(self, event_repo: EventRepository, artist_service: ArtistService):
        self.event_repo = event_repo
        self.artist_service = artist_service

    def create_event(
        self,
        event_name: str,
        description: str,
        duration: str,
        category: Category,
        artist_ids: list[str],
    ) -> Event:
        artists = self.artist_service.get_artists_batch(artist_ids)
        artist_names = [artist.name for artist in artists]
        event_id = str(uuid.uuid4())
        event_name = event_name.lower()
        event = Event(
            id=event_id,
            name=event_name,
            description=description,
            duration=duration,
            category=category.value if hasattr(category, "value") else category,
            is_blocked=False,
            artist_ids=artist_ids,
            artist_names=artist_names,
        )
        self.event_repo.add_event(event)
        return event

    def get_event_by_id(self, event_id: str) -> Event:
        event = self.event_repo.get_by_id(event_id=event_id)
        if not event:
            raise EventNotFound("invalid event id")
        return event

    def browse_events(self, event_name: str = "", city: str = "") -> Event:
        if not city:
            events = self.event_repo.get_events_by_name(event_name)
        else:
            events = self.event_repo.get_events_by_city_and_name(
                name=event_name, city=city
            )
        return events

    def get_host_events(self, host_id: str) -> List[Event]:
        events = self.event_repo.get_events_of_host(host_id=host_id)
        return events

    def update_event(self, event_id: str, update_req: UpdateEventRequest):
        self.event_repo.update_event(
            event_id=event_id, is_blocked=update_req.is_blocked
        )


# none present- bad request
# city presnt name absent -1
# city absent name present -2
# both present -1
