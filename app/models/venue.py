from dataclasses import dataclass


@dataclass
class Venue:
    id: str
    name: str
    host_id: str
    city: str
    state: str
    is_blocked: bool
    is_seat_layout_required: bool
