from repository.booking_repository import BookingRepository
from repository.show_repository import ShowRepository
from repository.event_repository import EventRepository
from repository.venue_repository import VenueRepository
from uuid import uuid4
from schemas.booking import BookingReq, BookingResponse
from models.booking import Booking
from typing import List


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
            pass
        event = self.event_repo.get_by_id(event_id=show.event_id)
        if event.is_blocked:
            pass
        venue = self.venue_repo.get_venue_by_id(venue_id=show.venue_id)
        if venue.is_blocked:
            pass
        booking_id = uuid4()
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
