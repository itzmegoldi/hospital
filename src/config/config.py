from pydantic import BaseModel
from src.config.aws import AwsConfig

from src.config.server import ServerConfig
from src.pkg.config import ConfigMixIn
from src.pkg.db import DatabaseConfig


class HospitalApiConfig(BaseModel):
    base_url: str = "https://hospital-directory.onrender.com/"


class Config(BaseModel, ConfigMixIn):
    database: DatabaseConfig
    server: ServerConfig
    aws: AwsConfig
    hospital_api: HospitalApiConfig
