from dataclasses import dataclass
from typing import List
from enum import Enum
class Category(Enum):
    MOVIE="movie"
    WORKSHOP="workshop"
    PARTY="party"
    
@dataclass
class Event:
    id: str
    name: str
    description: str
    duration: int
    category: str
    is_blocked: bool
    artist_ids: List[str]
    artist_names: List[str]

@dataclass
class EventDTO:
    event_id:str
    event_name:str
    description:str
    duration:str
    category:str
    is_blocked:bool
    artist_ids: List[str]
    artist_names: List[str]
