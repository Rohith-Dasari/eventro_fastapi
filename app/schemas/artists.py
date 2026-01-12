from pydantic import BaseModel


class CreateArtist(BaseModel):
    name: str
    bio: str


