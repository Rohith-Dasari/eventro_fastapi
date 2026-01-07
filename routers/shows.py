from fastapi import APIRouter, Depends, status
from dependencies import get_current_user, get_shows_service
from services.show_service import ShowService
from typing import Annotated
from schemas.shows import ShowCreateReq
shows_router = APIRouter(
    prefix="/shows", tags=["shows"], dependencies=[Depends(get_current_user)]
)

ShowServiceDep = Annotated[ShowService, Depends(get_shows_service)]

@shows_router.post("",status_code=status.HTTP_201_CREATED)
async def create_show(
    req:ShowCreateReq
)
