from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.deps import ErrorMiddleware, get_client, LoggerInitMiddleware
from src.api.v1 import router as v1_router
from src.builder.helper import fetch_config, fetch_config_and_build_services
from src.pkg import logging

logging.configure_logger(
    default_logger_names=[
        "root",
        "fastapi",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ]
)
logger = logging.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    fetch_config_and_build_services()
    yield


app = FastAPI(lifespan=lifespan)


class HealthCheckModel(BaseModel):
    status: str


@app.get("/health-check/", response_model=HealthCheckModel)
def health_check():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(middleware_class=ErrorMiddleware)
app.add_middleware(middleware_class=LoggerInitMiddleware)


app.include_router(v1_router)

if __name__ == "__main__":
    cfg = fetch_config()
    uvicorn.run(app, host=cfg.server.host, port=cfg.server.port, log_config=None)
