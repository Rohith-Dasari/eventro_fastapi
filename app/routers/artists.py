from fastapi import APIRouter, Depends
from dependencies import get_artist_service, require_roles
from schemas.artists import CreateArtist
from schemas.response import APIResponse

artist_router = APIRouter(prefix="/artists", tags=["artists"])
artist_roles_dep = require_roles(["admin", "host"])

@artist_router.get("/{artist_id}")
def get_artist_by_id(artist_id: str, artist_service=Depends(get_artist_service)):
    artist = artist_service.get_artist_by_id(artist_id)
    return APIResponse(status_code=200, message="retrieved successfully", data=artist)


@artist_router.post("", response_model=APIResponse)
def add_artist(
    payload: CreateArtist,
    current_user: dict = Depends(artist_roles_dep),
    artist_service=Depends(get_artist_service),
):
    artist = artist_service.add_artist(payload.name, payload.bio)
    return APIResponse(status_code=201, message="created successfully", data=artist)
