from repository.show_repository import ShowRepository
from repository.venue_repository import VenueRepository
from repository.event_repository import EventRepository
from custom_exceptions.generic import NotFoundException
from schemas.shows import ShowCreateReq, ShowUpdateReq, ShowResponse, VenuDTO
from models.shows import Show
from uuid import uuid4


class ShowService:
    def __init__(
        self,
        show_repo: ShowRepository,
        venue_repo: VenueRepository,
        event_repo: EventRepository,
    ):
        self.show_repo = show_repo
        self.venue_repo = venue_repo
        self.event_repo = event_repo

    def create_show(self, show_dto: ShowCreateReq):
        show_id = uuid4()
        show = Show(
            id=show_id,
            venue_id=show_dto.venue_id,
            event_id=show_dto.event_id,
            is_blocked=False,
            price=show_dto.price,
            show_date=show_dto.show_date,
            show_time=show_dto.show_time,
            booked_seats=[],
        )
        venue = self.venue_repo.get_venue_by_id(venue_id=show_dto.venue_id)
        event = self.event_repo.get_by_id(show_dto.event_id)

        self.show_repo.create_show(show=show, venue=venue, event=event)

    def get_show_by_id(self, show_id: str):
        show = self.show_repo.get_show_by_id(show_id)
        if not show:
            raise NotFoundException(
                resource="show", identifier=show_id, status_code=404
            )
        if show.is_blocked:
            raise NotFoundException(
                resource="show", identifier=show_id, status_code=404
            )
        venue = self.venue_repo.get_venue_by_id(show.venue_id)
        if venue.is_blocked:
            raise NotFoundException(
                resource="show", identifier=show_id, status_code=404
            )
        venue_dto = VenuDTO(
            venue_id=venue.id, venue_name=venue.name, city=venue.city, state=venue.state
        )
        return ShowResponse(
            id=show.id,
            event_id=show.event_id,
            price=show.price,
            show_date=show.show_date,
            show_time=show.show_time,
            booked_seats=show.booked_seats,
            venue=venue_dto,
            is_blocked=show.is_blocked,
            host_id=venue.host_id,
        )

    def update_show(self, show_id: str, req: ShowUpdateReq):
        show = self.show_repo.get_show_by_id(show_id)
        if not show:
            raise NotFoundException(
                resource="show", identifier=show_id, status_code=404
            )
        venue = self.venue_repo.get_venue_by_id(show.venue_id)
        if not venue:
            raise NotFoundException(
                resource="venue", identifier=show_id, status_code=404
            )
        return self.show_repo.update_show(
            show_id=show_id, is_blocked=req.is_blocked, venue=venue, show=show
        )

    def get_event_shows(self, event_id: str, city: str, date: str):
        return self.show_repo.list_by_event(event_id=event_id, city=city, date=date)
