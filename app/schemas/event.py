from pydantic import BaseModel, Field
from typing import List
from app.models.events import Category


class CreateEventRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    duration: int = Field(..., gt=0, description="Duration in minutes")
    category: Category
    artist_ids: List[str] = Field(..., min_length=1)


class UpdateEventRequest(BaseModel):
    is_blocked: bool
