from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, timedelta
import zoneinfo

LOCAL_TZ = "Europe/Kyiv"


class Slot(BaseModel):
    start: int
    end: int
    type: Literal["NotPlanned", "Definite"]

    def __str__(self):
        start_dt = (datetime.min + timedelta(minutes=self.start)).strftime("%H:%M")
        end_dt = (datetime.min + timedelta(minutes=self.end)).strftime("%H:%M")
        text_type = "Є світло 💡" if self.type == "NotPlanned" else "Немає світла ❌"
        return f"{text_type} з {start_dt} до {end_dt}"


class GroupInfo(BaseModel):
    date: datetime
    slots: list[Slot]

    def __str__(self):
        date_str = self.date.astimezone(zoneinfo.ZoneInfo(LOCAL_TZ)).strftime("%d.%m.%Y")
        slots_str = "\n".join([str(slot) for slot in self.slots])
        return f"{date_str}\n{slots_str}"


class PlanInfo(BaseModel):
    updated_on: datetime = Field(alias="updatedOn")
    today: GroupInfo
    tomorrow: GroupInfo

    def __str__(self):
        local_time = self.updated_on.astimezone(zoneinfo.ZoneInfo(LOCAL_TZ))
        return f"Оновлено: {local_time.strftime("%d.%m.%Y %H:%M:%S")}\n\nСьогодні:\n{self.today}\n\nЗавтра:\n{self.tomorrow}"
