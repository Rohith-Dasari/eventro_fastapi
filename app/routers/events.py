from fastapi import APIRouter, Depends, status, Query
from app.schemas.event import CreateEventRequest, UpdateEventRequest
from app.schemas.response import APIResponse
from app.services.event_service import EventService
from app.dependencies import require_roles, get_event_service, get_current_user
from typing import Optional, Annotated

event_router = APIRouter(
    prefix="/events", tags=["events"], dependencies=[Depends(get_current_user)]
)


@event_router.post("", status_code=status.HTTP_201_CREATED)
async def create_event(
    req: CreateEventRequest,
    current_user: dict = Depends(require_roles(["admin", "host"])),
    event_service: EventService = Depends(get_event_service),
):
    event = event_service.create_event(
        event_name=req.name,
        description=req.description,
        duration=req.duration,
        category=req.category,
        artist_ids=req.artist_ids,
    )
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="event successfully created",
        data=event,
    )


@event_router.get("/{event_id}")
async def get_event_by_id(
    event_id: str,
    event_service: EventService = Depends(get_event_service),
    
    user=Depends(get_current_user),
):
    event = event_service.get_event_by_id(event_id, user["role"])
    return APIResponse(status_code=200, message="successfully retrieved", data=event)


@event_router.get("")
async def browse_events(
    name: Annotated[Optional[str], Query(description="Event name to search")] = None,
    city: Annotated[Optional[str], Query(description="Event city to search")] = None,
    is_blocked: Optional[bool] = Query(None, description="Filter by blocked status"),
    user=Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
):
    #if both are not present error
    if name==None and city==None:
        raise ValueError("At least one of 'name' or 'city' query parameters must be provided.")
    
    #if name is not prese  but city is present, use city search
    if name == None:
        events=event_service.browse_events_by_city(city,is_blocked,user["role"])
        
    #if name  is present and city mmay or may not present
    else: 
        events = event_service.browse_events_by_name(
                    event_name=name, city=city, user_role=user["role"]
                )
    return APIResponse(status_code=200, message="successfully retrieved", data=events)


@event_router.patch("/{event_id}")
async def update_event(
    event_id: str,
    req: UpdateEventRequest,
    event_service: EventService = Depends(get_event_service),
    user=Depends(require_roles(["admin"])),
):
    event_service.update_event(event_id, req)
    return APIResponse(status_code=200, message=f"successfully updated {event_id}")
