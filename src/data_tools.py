from src.config import YasnoConfig, FileStorageConfig
from src.models import PlanInfo, OutagesPlan
from datetime import date
import requests
import orjson


class YasnoPlannedOutageParser:
    def __init__(self, config: YasnoConfig):
        self.config = config
        self.url = config.url.format(city_id=config.city_id, dso_id=config.dso_id)

    def parse(self) -> PlanInfo:
        response = requests.get(self.url)
        response.raise_for_status()
        data = response.json().get(self.config.group_id, {})
        return PlanInfo(**data)


class BaseInfoStorage:
    def save_plan(self, plan: OutagesPlan):
        raise NotImplementedError

    def read_plan(self, plan_date: date) -> OutagesPlan | None:
        raise NotImplementedError


class FileInfoStorage(BaseInfoStorage):
    def __init__(self, config: FileStorageConfig):
        self.config = config

    def read_plan(self, plan_date: date) -> OutagesPlan | None:
        date_str = plan_date.strftime("%d.%m.%Y")
        try:
            with open(f"{self.config.path}/plan_{date_str}.json", "rb") as f:
                data = orjson.loads(f.read())
                return OutagesPlan.model_validate(data)
        except FileNotFoundError:
            return None

    def save_plan(self, plan: OutagesPlan):
        date_str = plan.date.strftime("%d.%m.%Y")
        with open(f"{self.config.path}/plan_{date_str}.json", "wb+") as f:
            f.write(orjson.dumps(plan.model_dump()))


class OutagesPlanDiffChecker:
    @staticmethod
    def has_changes(old_plan: OutagesPlan, new_plan: OutagesPlan) -> bool:
        return (old_plan.updated_on != new_plan.updated_on) and (old_plan.slots != new_plan.slots)
