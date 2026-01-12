from pydantic import BaseModel
from typing import Optional, List, Dict


class ShowCreateReq(BaseModel):
    event_id: str
    venue_id: str
    price: int
    show_date: str
    show_time: str


class ShowUpdateReq(BaseModel):
    is_blocked: bool


class VenuDTO(BaseModel):
    venue_id: str
    venue_name: str
    city: str
    state: str


class ShowResponse(BaseModel):
    id: str
    event_id: str
    price: int
    show_date: str
    show_time: str
    booked_seats: List
    venue: VenuDTO
    is_blocked: bool
    host_id: str
