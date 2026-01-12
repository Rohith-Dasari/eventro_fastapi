from app.repository.booking_repository import BookingRepository
from app.repository.show_repository import ShowRepository
from app.repository.event_repository import EventRepository
from app.repository.venue_repository import VenueRepository
from uuid import uuid4
from app.schemas.booking import BookingReq, BookingResponse
from app.models.booking import Booking
from typing import List
from app.custom_exceptions.generic import BlockedResource
from app.custom_exceptions.booking_exceptions import SeatAlreadyBookedException


class BookingService:
    def __init__(
        self,
        booking_repo: BookingRepository,
        show_repo: ShowRepository,
        event_repo: EventRepository,
        venue_repo: VenueRepository,
    ):
        self.booking_repo = booking_repo
        self.event_repo = event_repo
        self.show_repo = show_repo
        self.venue_repo = venue_repo

    def create_booking(self, req: BookingReq, user_id: str) -> BookingResponse:

        show = self.show_repo.get_show_by_id(show_id=req.show_id)
        if show.is_blocked:
            raise BlockedResource(resource="show", identifier=show.id, status_code=403)
        booked_seats = set(show.booked_seats)
        requested_seats = set(req.seats)
        if booked_seats.intersection(requested_seats):
            raise SeatAlreadyBookedException(
                f" {booked_seats.intersection(requested_seats)} seats already booked"
            )
        event = self.event_repo.get_by_id(event_id=show.event_id)
        if event.is_blocked:
            raise BlockedResource(
                resource="event", identifier=event.id, status_code=403
            )
        venue = self.venue_repo.get_venue_by_id(venue_id=show.venue_id)
        if venue.is_blocked:
            raise BlockedResource(
                resource="venue", identifier=venue.id, status_code=403
            )
        booking_id = str(uuid4())
        current_time = ""
        total_price = len(req.seats) * show.price
        booking = Booking(
            booking_id=booking_id,
            user_id=user_id,
            show_id=req.show_id,
            time_booked=current_time,
            total_booking_price=total_price,
            seats=req.seats,
        )
        self.booking_repo.add_booking(
            venue=venue, event=event, show=show, booking=booking
        )
        booking_dto = BookingResponse(
            user_id=user_id,
            booking_date=show.show_date,
            booking_id=booking_id,
            show_id=show.id,
            time_booked=current_time,
            total_price=total_price,
            seats=req.seats,
            venue_city=venue.city,
            venue_name=venue.name,
            venue_state=venue.state,
            event_name=event.name,
            event_duration=event.duration,
            event_id=event.id,
        )
        return booking_dto

    def get_user_bookings(self, user_id: str) -> List[BookingResponse]:
        bookings = self.booking_repo.get_bookings(user_id=user_id)
        return bookings
