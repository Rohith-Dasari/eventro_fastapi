from services.artist_service import ArtistService
from repository.event_repository import EventRepository
from models.events import Category, Event
from custom_exceptions.event_exceptions import EventNotFound
import uuid


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
    ):
        artists = self.artist_service.get_artists_batch(artist_ids)
        artist_names = [artist.name for artist in artists]
        event_id = str(uuid.uuid4())
        event_name=event_name.lower()
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
    
    
    def get_event_by_name(self, event_name:str)->Event:
        events=self.event_repo.get_events_by_name(event_name)
        if len(events)==0:
            raise EventNotFound(f"no events found with {event_name}")
        return events
        
