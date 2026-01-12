from services.artist_service import ArtistService
from repository.event_repository import EventRepository
from models.events import Category, Event
from custom_exceptions.generic import NotFoundException
import uuid
from typing import List,Optional
from schemas.event import UpdateEventRequest
from models.users import Role


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

    def get_event_by_id(self, event_id: str, user_role) -> Event:
        event = self.event_repo.get_by_id(event_id=event_id)
        if not event:
            raise NotFoundException("event", event_id, status_code=404)
        if event.is_blocked:
            if user_role != Role.ADMIN.value:
                raise NotFoundException("event", event_id, status_code=404)
        return event

    def browse_events_by_city(
        self, city: Optional[str] = None, is_blocked: Optional[bool] = None, user_role: str=""
    ) -> List[Event]:
        events = self.event_repo.get_events_by_city_and_name(
             city=city
        )
        if user_role != Role.ADMIN.value or is_blocked==False:
            events = [event for event in events if not event.is_blocked]
        elif user_role == Role.ADMIN.value and is_blocked==True:
            events = [event for event in events if event.is_blocked]
        return events
    
    def browse_events_by_name(
        self, user_role: str, event_name: Optional[str] = None, city: Optional[str] = None
    ) -> List[Event]:
        if city==None or user_role!=Role.CUSTOMER.value:
            events = self.event_repo.get_events_by_name(event_name)
        elif city!=None and user_role==Role.CUSTOMER.value:
            events = self.event_repo.get_events_by_city_and_name(
                    name=event_name, city=city
                )
        if user_role != Role.ADMIN.value:
            events = [event for event in events if not event.is_blocked]
        return events
        

    def get_host_events(self, host_id: str) -> List[Event]:
        events = self.event_repo.get_events_of_host(host_id=host_id)
        return events

    def update_event(self, event_id: str, update_req: UpdateEventRequest):
        self.event_repo.update_event(
            event_id=event_id, is_blocked=update_req.is_blocked
        )


