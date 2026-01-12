from app.repository.show_repository import ShowRepository
from app.repository.venue_repository import VenueRepository
from app.repository.event_repository import EventRepository
from app.custom_exceptions.generic import NotFoundException
from app.schemas.shows import ShowCreateReq, ShowUpdateReq, ShowResponse, VenuDTO
from app.models.shows import Show
from uuid import uuid4
from typing import Optional
from app.models.users import Role


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
        if not venue:
            pass
        event = self.event_repo.get_by_id(show_dto.event_id)
        if not event:
            pass

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

    def get_event_shows(self, event_id: str, city: str, user, date: Optional[str]=None):
        city=city.lower()
        #1 date not mentioned
        if date==None:
            shows= self.show_repo.list_by_event_city(event_id=event_id, city=city)
        # date mentioned
        else: 
            shows= self.show_repo.list_by_event_date(event_id=event_id, city=city, date=date)
        if not shows:
            return []
        if user["role"]==Role.CUSTOMER.value:
            shows= [show for show in shows if not show.is_blocked]
        if not shows:
            return []
        venue_ids= list(set([show.venue_id for show in shows]))
        if not venue_ids:
            return []
        venues=self.venue_repo.batch_get_venues(venue_ids=venue_ids)
        #batchget venues for shows
        show_dtos=[]
        for show in shows:
            venue_dto=None
            for venue in venues:
                if venue.is_blocked:
                    continue
                if venue.id==show.venue_id:
                    venue_dto= VenuDTO(
                        venue_id=venue.id,
                        venue_name=venue.name,
                        city=venue.city,
                        state=venue.state,
                    )
                    break
                
            show_dto=ShowResponse(
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
            if user["role"]==Role.HOST.value:
                if venue.host_id!=user["user_id"]:
                    continue
            show_dtos.append(show_dto)
        return show_dtos
    