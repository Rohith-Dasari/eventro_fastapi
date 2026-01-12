from fastapi import APIRouter, Depends, status
from app.dependencies import get_current_user, get_show_service, require_roles
from app.services.show_service import ShowService
from typing import Annotated, Optional
from app.schemas.shows import ShowCreateReq, ShowUpdateReq
from app.schemas.response import APIResponse

shows_router = APIRouter(
    prefix="/shows", tags=["shows"], dependencies=[Depends(get_current_user)]
)

ShowServiceDep = Annotated[ShowService, Depends(get_show_service)]


@shows_router.post("", status_code=status.HTTP_201_CREATED)
async def create_show(
    req: ShowCreateReq,
    current_user: dict = Depends(require_roles(["host"])),
    show_service: ShowService = Depends(get_show_service),
):
    show_service.create_show(show_dto=req)
    return APIResponse(
        status_code=status.HTTP_201_CREATED, message="created show successfully"
    )


@shows_router.get("/{show_id}", status_code=status.HTTP_200_OK)
def get_show_by_id(
    show_id: str, show_service: ShowService = Depends(get_show_service)
):
    show_response = show_service.get_show_by_id(show_id)
    return APIResponse(
        status_code=200, message=f"successfully retrieved show", data=show_response
    )


@shows_router.get("", status_code=status.HTTP_200_OK)
def event_shows(
    event_id: str,
    city: str,
    date: Optional[str]=None,
    host_id: Optional[str]=None,
    show_service: ShowService = Depends(get_show_service),
    user=Depends(get_current_user),
):
    if host_id!=None:
        if user["role"]!="host" or user["user_id"]!=host_id:
            return APIResponse(
                status_code=403,
                message="forbidden: only host can access their shows",
            )
    show_responses = show_service.get_event_shows(event_id, city.lower(),user, date)
    return APIResponse(
        status_code=200, message=f"successfully retrieved shows", data=show_responses
    )


@shows_router.patch("/{show_id}", status_code=status.HTTP_200_OK)
def update_show(
    show_id: str,
    req: ShowUpdateReq,
    current_user: dict = Depends(require_roles(["host"])),
    show_service: ShowService = Depends(get_show_service),
):
    show_responses = show_service.update_show(show_id=show_id, req=req)
    return APIResponse(
        status_code=200,
        message=f"successfully updated show",
    )
