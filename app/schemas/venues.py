from pydantic import BaseModel, Field
from typing import Optional


class VenueCreateReq(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=20)
    state: str = Field(..., min_length=1, max_length=20)
    is_seat_layout_required: Optional[bool]=True


class VenueUpdateReq(BaseModel):
    is_blocked: bool
