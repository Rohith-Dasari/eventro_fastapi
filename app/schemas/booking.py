from pydantic import BaseModel
from typing import List, Optional


class BookingReq(BaseModel):
    show_id: str
    seats: List[str]
    user_id: Optional[str] = None


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
    event_duration: int
    event_id: str
