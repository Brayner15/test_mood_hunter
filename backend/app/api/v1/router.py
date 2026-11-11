from fastapi import APIRouter

from app.api.v1 import requests, statuses

api_router = APIRouter()
api_router.include_router(requests.router, prefix="/requests", tags=["solicitudes"])
api_router.include_router(statuses.router, prefix="/statuses", tags=["estados"])
