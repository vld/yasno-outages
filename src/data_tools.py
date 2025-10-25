from src.config import YasnoConfig, MySQLConfig
from src.models import PlanInfo, OutagesPlan, Slot
from datetime import date
import atexit
import requests
import mariadb
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


class PlanDB:
    def __init__(self, config: MySQLConfig):
        self.config = config
        self._connection = None
        atexit.register(self.close)

    def get_connection(self):
        if self._connection is None:
            self._connection = mariadb.connect(
                user=self.config.user,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
            )
        return self._connection

    def read_plan(self, plan_date: date) -> OutagesPlan | None:
        with mariadb.connect(
            user=self.config.user,
            password=self.config.password,
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
        ) as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = "SELECT * FROM plans WHERE date = %s"
                cursor.execute(query, (plan_date,))
                result = cursor.fetchone()
        if result:
            result["slots"] = orjson.loads(result["slots"])
            return OutagesPlan.model_validate(result)
        return None

    def save_plan(self, plan: OutagesPlan):
        with mariadb.connect(
            user=self.config.user,
            password=self.config.password,
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
        ) as conn:
            with conn.cursor() as cursor:
                query = """
                INSERT INTO plans (date, updated_on, slots)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    updated_on = VALUES(updated_on),
                    slots = VALUES(slots)
                """
                slots_json = orjson.dumps([slot.model_dump() for slot in plan.slots])
                cursor.execute(query, (plan.date, plan.updated_on, slots_json))
            conn.commit()

    def close(self):
        if self._connection:
            self._connection.close()


class OutagesPlanDiffChecker:
    @staticmethod
    def has_changes(old_plan: OutagesPlan, new_plan: OutagesPlan) -> bool:
        return old_plan.slots != new_plan.slots
