from dataclasses import dataclass
from typing import Optional

@dataclass
class Artist:
    id: str
    name: str
    bio: Optional[str] = None
