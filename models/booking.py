from dataclasses import dataclass
from typing import List


@dataclass
class Booking:
    booking_id: str
    user_id: str
    show_id: str
    time_booked: str
    total_booking_price: str
    seats: List[str]
