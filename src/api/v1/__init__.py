from fastapi import APIRouter
from src.api.v1.hostpitals import router as hospital_router


router = APIRouter(prefix="/v1")

router.include_router(hospital_router)
