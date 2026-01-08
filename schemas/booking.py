from pydantic import BaseModel
from typing import List


class BookingReq(BaseModel):
    show_id: str
    seats: List[str]


class BookingResponse(BaseModel):
    user_id: str
    booking_date: str
    booking_id: str
    show_id: str
    time_booked: str
    total_price: int
    seats: List[str]
    venue_city: str
    venue_name: str
    venue_state: str
    event_name: str
    event_duration: str
    event_id: str
