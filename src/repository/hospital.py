from typing import Protocol, Optional, List
import uuid
from sqlalchemy.orm import Session
from src.pkg.db import IHandler
from src.models.hospitals_files import HospitalFiles, FileStatus

class IHospitalRepo(Protocol):
    def create_file_record(self, batch_id: str, filename: str) -> HospitalFiles: ...
    def update_file_status(self, batch_id: str, status: str, response: dict = None) -> None: ...
    def get_file_by_batch_id(self, batch_id: str) -> Optional[HospitalFiles]: ...
    def get_pending_records(self) -> List[HospitalFiles]: ...

class HospitalRepo(IHospitalRepo):
    def __init__(self, db_handler: IHandler):
        self.db_handler = db_handler

    def create_file_record(self, batch_id: str, filename: str) -> HospitalFiles:
        session = self.db_handler.get_session()
        record = HospitalFiles(
            batch_id=batch_id,
            file=filename,
            status=FileStatus.INITIATED.value
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        session.close()
        return record

    def update_file_status(self, batch_id: str, status: str, response: dict = None) -> None:
        session = self.db_handler.get_session()
        record = session.query(HospitalFiles).filter_by(batch_id=batch_id).first()
        if record:
            record.status = status
            if response is not None:
                record.response = response
            session.commit()
        session.close()

    def get_file_by_batch_id(self, batch_id: str) -> Optional[HospitalFiles]:
        session = self.db_handler.get_session()
        record = session.query(HospitalFiles).filter_by(batch_id=batch_id).first()
        session.close()
        return record

    def get_pending_records(self) -> List[HospitalFiles]:
        session = self.db_handler.get_session()
        # Filter records where status is either PROCESSING or FAILED
        records = session.query(HospitalFiles).filter(
            HospitalFiles.status.in_([FileStatus.PROCESSING.value, FileStatus.FAILED.value])
        ).all()
        session.close()
        return records
