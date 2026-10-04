from src.pkg.db import IHandler
from src.repository.hospital import HospitalRepo, IHospitalRepo

from typing_extensions import Self


class Repos:
    def with_hospital_repo(self, db_handler: IHandler) -> Self:
        self.hospital_repo: IHospitalRepo = HospitalRepo(db_handler=db_handler)
        return self
