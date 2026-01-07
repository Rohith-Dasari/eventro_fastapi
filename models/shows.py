from dataclasses import dataclass
import time


@dataclass
class Show:
    id: str
    venue_id: str
    event_id: str
    is_blocked: bool
    price: float
    show_date: str
    show_time: str
    booked_seats: str
