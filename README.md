# Hospital Bulk Upload API

This API provides functionality to bulk upload hospital data via CSV files, integrating with an external Hospital Directory API. It features a robust processing pipeline with local tracking, file persistence, and the ability to resume failed or stalled uploads.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose installed.
- A `.env` file in the root directory with the following variables:
  - `APP_ENV=local`
  - `DB_USERNAME=dbuser`
  - `DB_PASSWORD=root123`
  - `DB_NAME=hospital`
  - `DB_URL=localhost`
  - `DB_PORT=5432`

### Startup using Docker Compose
Run the following command to build and start the API and Database:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

---

## 🛠 API Reference

### 1. Bulk Upload Hospitals
Uploads a CSV file, generates a unique batch ID, and streams the processing progress.

- **Endpoint**: `POST /v1/hospitals/bulk`
- **Content-Type**: `multipart/form-data`
- **Payload**: `file` (CSV file)
- **CSV Format**: `name,address,phone` (phone is optional)
- **Response**: `application/x-ndjson` (Streaming events)

#### Curl Example:
```bash
curl -X POST "http://localhost:8000/v1/hospitals/bulk" \
     -F "file=@/path/to/your/hospitals.csv" \
     -N
```

---

### 2. Resume Pending Uploads
Scans the database for any records with status `processing` or `failed` and re-processes them using the locally stored files.

- **Endpoint**: `POST /v1/hospitals/bulk/resume`
- **Response**: `application/x-ndjson` (Streaming events for all resumed batches)

#### Curl Example:
```bash
curl -X POST "http://localhost:8000/v1/hospitals/bulk/resume" \
     -N
```

---

### 3. Health Check
Verify if the API is running.

- **Endpoint**: `GET /health-check/`
- **Response**: `{"status": "ok"}`

#### Curl Example:
```bash
curl "http://localhost:8000/health-check/"
```

---

## ⚙️ Technical Workflow

1. **Validation**: The API validates the CSV structure and extensions.
2. **Tracking**: A record is created in the `hospital_files` table with a unique `batch_id`.
3. **Persistence**: The CSV file is saved locally in `app/uploads/{batch_id}_{filename}`.
4. **External Integration**:
   - Each row is sent to `POST /hospitals/` on the external directory API.
   - Once all rows are processed, a `PATCH /hospitals/batch/{batch_id}/activate` call is made.
   - A `GET /hospitals/batch/{batch_id}` call retrieves the final created hospitals.
5. **Streaming**: The client receives real-time progress (percentage, row count) via NDJSON.
6. **Completion**: The local record is updated with a comprehensive summary including processing time and success/failure counts.

## 📂 Project Structure
- `src/api`: FastAPI routes and app initialization.
- `src/service`: Core business logic and external API integration.
- `src/repository`: Database access layer.
- `src/models`: SQLAlchemy database models.
- `src/builder`: Dependency injection and object factory.
- `src/pkg`: Shared utilities (DB, Config, Logging).
- `app/uploads`: Local storage for uploaded CSVs.
