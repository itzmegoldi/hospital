import os
import uuid
from typing import AsyncGenerator, Protocol

import pandas as pd
from src.builder import Clients
from src.config.config import Config
from src.models.hospitals_files import FileStatus
from src.repository.hospital import IHospitalRepo


class IHospitalService(Protocol):
    async def process_bulk_upload(
        self, filename: str, contents: bytes
    ) -> AsyncGenerator[dict, None]: ...


class HospitalService(IHospitalService):
    def __init__(self, config: Config, clients: Clients, repo: IHospitalRepo):
        self.config = config
        self.clients = clients
        self.repo = repo
        self.upload_dir = "app/uploads"

    async def process_bulk_upload(
        self, filename: str, contents: bytes
    ) -> AsyncGenerator[dict, None]:
        batch_id = str(uuid.uuid4())

        # 1. Create initial record
        self.repo.create_file_record(batch_id, filename)

        # 2. Save file to app dir using batch_id
        file_path = os.path.join(self.upload_dir, f"{batch_id}_{filename}")
        with open(file_path, "wb") as f:
            f.write(contents)

        # 3. Update status to PROCESSING
        self.repo.update_file_status(batch_id, FileStatus.PROCESSING.value)

        try:
            # 4. Stream processing
            # We assume the contents is a CSV. We'll read it and yield progress.
            import io

            df = pd.read_csv(io.BytesIO(contents))
            total_rows = len(df)
            processed_rows = 0

            for index, row in df.iterrows():
                # Simulate some processing logic here
                processed_rows += 1
                yield {
                    "batch_id": batch_id,
                    "progress": f"{processed_rows}/{total_rows}",
                    "percentage": round((processed_rows / total_rows) * 100, 2),
                    "status": "processing",
                }

            # 5. Mark as COMPLETED
            self.repo.update_file_status(
                batch_id,
                FileStatus.COMPLETED.value,
                response={"rows_processed": total_rows},
            )
            yield {
                "batch_id": batch_id,
                "status": FileStatus.COMPLETED.value,
                "message": "Processing completed successfully",
            }

        except Exception as e:
            self.repo.update_file_status(
                batch_id, FileStatus.FAILED.value, response={"error": str(e)}
            )
            yield {
                "batch_id": batch_id,
                "status": FileStatus.FAILED.value,
                "error": str(e),
            }
