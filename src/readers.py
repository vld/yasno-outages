from src.config import YasnoConfig
from src.models import PlanInfo
import requests


class YasnoPlannedOutageParser:
    def __init__(self, config: YasnoConfig):
        self.config = config
        self.url = config.url.format(city_id=config.city_id, dso_id=config.dso_id)

    def parse(self) -> PlanInfo:
        response = requests.get(self.url)
        response.raise_for_status()
        data = response.json().get(self.config.group_id, {})
        return PlanInfo(**data)


class SQLDBReader: ...
