from enum import Enum

from sqlalchemy import BigInteger, Column, JSON, String, text
from src.pkg.db import BaseModel


class FileStatus(Enum):
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HospitalFiles(BaseModel):
    __tablename__ = "hospital_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_id = Column(String, unique=True)
    file = Column(String, nullable=False)
    response = Column(
        JSON,
        default=dict,
        server_default=text("'{}'::json"),
    )
    status = Column(
        String,
        default=FileStatus.INITIATED.value,
        server_default=FileStatus.INITIATED.value,
    )
