from fastapi import APIRouter, Depends, HTTPException, status
from schemas.event import CreateEventRequest
from schemas.response  import APIResponse
from services.event_service import EventService
from custom_exceptions.artist_exceptions import InvalidArtistID
from dependencies import require_roles,get_event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_event(
    req: CreateEventRequest,
    current_user: dict = Depends(require_roles(["admin", "host"])),
    event_service: EventService = Depends(get_event_service)
):
    try:
        event = event_service.create_event(
            event_name=req.name,
            description=req.description,
            duration=req.duration,
            category=req.category,
            artist_ids=req.artist_ids,
        )
        return APIResponse(status_code=status.HTTP_201_CREATED,message="event successfully created",data=event)
    except InvalidArtistID as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
        
@router.get("/{event_id}")
def get_event_by_id(
    event_id: str,
    event_service: EventService = Depends(),
):
    event = event_service.get_event_by_id(event_id)
    return APIResponse(status_code=200,message="successfully retrieved",data=event)
