from src.config import YasnoConfig, FileStorageConfig
from src.consts import *
from src.models import PlanInfo, OutagesPlan, MonitoringInfo
from datetime import date
import requests
import orjson


class YasnoPlannedOutageParser:
    def __init__(self, config: YasnoConfig):
        self.config = config
        self.group_id = None
        self.session = requests.Session()

    def _get_street_id(self) -> int:
        response = self.session.get(
            YASNO_STREETS_URL,
            params={"regionId": self.config.city_id, "query": self.config.street_name, "dsoId": self.config.dso_id},
            timeout=YASNO_API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"Street '{self.config.street_name}' not found")
        return data[0].get("id")

    def _get_house_id(self, street_id: int) -> int:
        response = self.session.get(
            YASNO_HOUSES_URL,
            params={
                "regionId": self.config.city_id,
                "streetId": street_id,
                "query": self.config.house_number,
                "dsoId": self.config.dso_id,
            },
            timeout=YASNO_API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"House '{self.config.house_number}' not found on street id {street_id}")
        return data[0].get("id")

    def get_group_id(self) -> str:
        if self.group_id:
            return self.group_id
        street_id = self._get_street_id()
        house_id = self._get_house_id(street_id)
        response = self.session.get(
            YASNO_GROUP_URL,
            params={
                "regionId": self.config.city_id,
                "streetId": street_id,
                "houseId": house_id,
                "dsoId": self.config.dso_id,
            },
            timeout=YASNO_API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        self.group_id = ".".join([str(data.get("group")), str(data.get("subgroup"))])
        return self.group_id

    def parse(self) -> PlanInfo:
        response = self.session.get(
            YASNO_PLAN_URL.format(city_id=self.config.city_id, dso_id=self.config.dso_id), timeout=YASNO_API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json().get(self.get_group_id(), {})
        return PlanInfo(**data)


class BaseInfoStorage:
    def save_plan(self, plan: OutagesPlan):
        raise NotImplementedError

    def read(self, object_date: date, name_prefix: str = "plan") -> OutagesPlan | MonitoringInfo | None:
        raise NotImplementedError

    def save_monitoring(self, monitoring: MonitoringInfo):
        raise NotImplementedError


class FileInfoStorage(BaseInfoStorage):
    def __init__(self, config: FileStorageConfig):
        self.config = config

    def read(self, object_date: date, name_prefix: str = "plan") -> OutagesPlan | MonitoringInfo | None:
        date_str = object_date.strftime("%d.%m.%Y")
        try:
            with open(f"{self.config.path}/{name_prefix}_{date_str}.json", "rb") as f:
                data = orjson.loads(f.read())
                if name_prefix == "plan":
                    return OutagesPlan.model_validate(data)
                elif name_prefix == "monitoring":
                    return MonitoringInfo.model_validate(data)
                else:
                    raise ValueError(f"Unknown name_prefix: {name_prefix}")
        except FileNotFoundError:
            return None

    def save_plan(self, plan: OutagesPlan):
        date_str = plan.date.strftime("%d.%m.%Y")
        with open(f"{self.config.path}/plan_{date_str}.json", "wb+") as f:
            f.write(orjson.dumps(plan.model_dump()))

    def save_monitoring(self, monitoring: MonitoringInfo):
        date_str = monitoring.date.strftime("%d.%m.%Y")
        with open(f"{self.config.path}/monitoring_{date_str}.json", "wb+") as f:
            f.write(orjson.dumps(monitoring.model_dump()))


class OutagesPlanDiffChecker:
    @staticmethod
    def has_changes(old_plan: OutagesPlan, new_plan: OutagesPlan) -> bool:
        return (old_plan.updated_on != new_plan.updated_on) and (old_plan.slots != new_plan.slots)
