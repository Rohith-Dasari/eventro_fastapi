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
    price: str
    show_date: str
    show_time: str
    booked_seats: List
    venue: VenuDTO
    is_blocked: bool
    host_id: str


"""{
            "id": "12b6e6b3-c8db-4b69-9d89-975894fd66c1",
            "event_id": "3e43d9ae-4d02-443e-8f01-3fac459c329f",
            "price": 100,
            "show_date": "2026-01-08T00:00:00Z",
            "show_time": "18:02",
            "booked_seats": [],
            "venue": {
                "venue_id": "1f831112-ec5e-4b46-976d-ff19235a70f7",
                "venue_name": "gulshan",
                "city": "noida",
                "state": "uttar pradesh"
            },
            "is_blocked": false,
            "host_id": "host@gmail.com"
        }"""
