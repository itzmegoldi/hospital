import os
import uuid
import pandas as pd
import httpx
import io
import time
from typing import AsyncGenerator, Protocol, List
from src.builder import Clients
from src.config.config import Config
from src.repository.hospital import IHospitalRepo
from src.models.hospitals_files import FileStatus

class IHospitalService(Protocol):
    async def process_bulk_upload(self, filename: str, contents: bytes) -> AsyncGenerator[dict, None]: ...
    async def resume_pending_uploads(self) -> AsyncGenerator[dict, None]: ...

class HospitalService:
    def __init__(self, config: Config, clients: Clients, repo: IHospitalRepo):
        self.config = config
        self.clients = clients
        self.repo = repo
        self.upload_dir = "app/uploads"

    async def _execute_processing_flow(self, batch_id: str, filename: str, contents: bytes) -> AsyncGenerator[dict, None]:
        """
        Repeatable core logic for processing CSV and calling External API.
        """
        start_time = time.time()
        
        self.repo.update_file_status(batch_id, FileStatus.PROCESSING.value)
        
        try:
            base_url = self.config.hospital_api.base_url.rstrip("/")
            df = pd.read_csv(io.BytesIO(contents))
            total_rows = len(df)
            processed_rows = 0
            failed_count = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for index, row in df.iterrows():
                    payload = {
                        "name": row.get("name"),
                        "address": row.get("address"),
                        "phone": row.get("phone"),
                        "creation_batch_id": batch_id
                    }
                    
                    try:
                        response = await client.post(f"{base_url}/hospitals/", json=payload)
                        if response.status_code >= 400:
                            failed_count += 1
                    except Exception:
                        failed_count += 1
                    
                    processed_rows += 1
                    yield {
                        "batch_id": batch_id,
                        "progress": f"{processed_rows}/{total_rows}",
                        "percentage": round((processed_rows / total_rows) * 100, 2),
                        "status": "processing"
                    }
                
                try:
                    activate_res = await client.patch(f"{base_url}/hospitals/batch/{batch_id}/activate")
                    batch_activated = activate_res.status_code < 300
                except Exception:
                    batch_activated = False
                
                hospitals_list = []
                if batch_activated:
                    try:
                        list_res = await client.get(f"{base_url}/hospitals/batch/{batch_id}")
                        if list_res.status_code < 300:
                            api_hospitals = list_res.json()
                            for i, h in enumerate(api_hospitals):
                                hospitals_list.append({
                                    "row": i + 1,
                                    "hospital_id": h.get("id"),
                                    "name": h.get("name"),
                                    "status": "created_and_activated" if batch_activated else "created"
                                })
                    except Exception:
                        pass

            processing_time = int(time.time() - start_time)
            result_summary = {
                "batch_id": batch_id,
                "total_hospitals": total_rows,
                "processed_hospitals": processed_rows,
                "failed_hospitals": failed_count,
                "processing_time_seconds": processing_time,
                "batch_activated": batch_activated,
                "hospitals": hospitals_list
            }
            
            self.repo.update_file_status(batch_id, FileStatus.COMPLETED.value, response=result_summary)
            
            yield {
                "batch_id": batch_id,
                "status": FileStatus.COMPLETED.value,
                "message": "Processing completed",
                "summary": result_summary
            }
            
        except Exception as e:
            self.repo.update_file_status(batch_id, FileStatus.FAILED.value, response={"error": str(e)})
            yield {
                "batch_id": batch_id,
                "status": FileStatus.FAILED.value,
                "error": str(e)
            }

    async def process_bulk_upload(self, filename: str, contents: bytes) -> AsyncGenerator[dict, None]:
        batch_id = str(uuid.uuid4())
        self.repo.create_file_record(batch_id, filename)
        
        os.makedirs(self.upload_dir, exist_ok=True)
        file_path = os.path.join(self.upload_dir, f"{batch_id}_{filename}")
        with open(file_path, "wb") as f:
            f.write(contents)
            
        async for event in self._execute_processing_flow(batch_id, filename, contents):
            yield event

    async def resume_pending_uploads(self) -> AsyncGenerator[dict, None]:
        # 1. Pick records from table which are PROCESSING or FAILED
        pending_records = self.repo.get_pending_records()
        
        if not pending_records:
            yield {"message": "No pending or failed records found to resume."}
            return

        for record in pending_records:
            # 2. Pick the file using the batch id from the app dir
            file_path = os.path.join(self.upload_dir, f"{record.batch_id}_{record.file}")
            if not os.path.exists(file_path):
                yield {"batch_id": record.batch_id, "status": "error", "message": f"File not found: {file_path}"}
                continue
                
            with open(file_path, "rb") as f:
                contents = f.read()
            
            # 3. Reprocess using the same flow
            async for event in self._execute_processing_flow(record.batch_id, record.file, contents):
                yield event
