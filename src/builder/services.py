from src.builder import Clients
from src.config.config import Config
from src.repository.hospital import IHospitalRepo
from src.service.hospital import HospitalService, IHospitalService
from typing_extensions import Self


class Services:
    def with_hospital_service(
        self, config: Config, clients: Clients, repo: IHospitalRepo
    ) -> Self:
        self.hospital_service: IHospitalService = HospitalService(
            config=config, clients=clients, repo=repo
        )
        return self
