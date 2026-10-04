from io import BytesIO
from typing import Annotated
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse
import json

from src.builder import get_services
from src.service.hospital import IHospitalService

router = APIRouter(prefix="/hospitals")

def get_hospital_service():
    return get_services().hospital_service

HOSPITALSERVICEDEP = Annotated[IHospitalService, Depends(get_hospital_service)]

EXPECTED_COLUMNS = {"name", "address", "phone"}

def validate_hospital_csv(contents: bytes) -> pd.DataFrame:
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty.",
        )

    try:
        df = pd.read_csv(BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file.",
        )

    actual_columns = set(df.columns)
    missing_columns = EXPECTED_COLUMNS - actual_columns
    unexpected_columns = actual_columns - EXPECTED_COLUMNS

    if missing_columns or unexpected_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Invalid CSV columns.",
                "missing_columns": sorted(missing_columns),
                "unexpected_columns": sorted(unexpected_columns),
                "expected_columns": sorted(EXPECTED_COLUMNS),
            },
        )

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV does not contain any data rows.",
        )

    return df

@router.post("/bulk")
async def bulk_upload_hospitals(
    service: HOSPITALSERVICEDEP, file: UploadFile = File(...)
):
    try:
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are allowed.",
            )

        contents = await file.read()
        validate_hospital_csv(contents)

        # We return a StreamingResponse that consumes the generator from the service
        async def event_generator():
            async for event in service.process_bulk_upload(file.filename, contents):
                yield json.dumps(event) + "\n"

        return StreamingResponse(event_generator(), media_type="application/x-ndjson")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process hospital CSV: {str(e)}",
        )
