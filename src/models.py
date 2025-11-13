from pydantic import BaseModel, Field, model_validator
from typing import Literal
from typing_extensions import Self
from datetime import datetime, timedelta
from enum import Enum
import logging


logger = logging.getLogger("YasnoOutageMonitor")


class DayStat(BaseModel):
    outages_minutes: int
    power_minutes: int

    @model_validator(mode="before")
    @classmethod
    def total_minutes(cls, v) -> Self:
        total = v["outages_minutes"] + v["power_minutes"]
        if total != 1440:
            raise ValueError("Total minutes in a day is not 1440, got %d", total)
        return v

    def __str__(self) -> str:
        return (
            "\nВсього за день:\n"
            f"❌ Світла немає: {self.outages_minutes // 60} год. {self.outages_minutes % 60} хв.\n"
            f"⚡️ Світло є: {self.power_minutes // 60} год. {self.power_minutes % 60} хв."
        )


class NotificationType(str, Enum):
    PLAN_NEW = "PlanNew"
    PLAN_CHANGED = "PlanChanged"
    PLAN_STABLE = "PlanStable"


class Slot(BaseModel):
    start: int
    end: int
    type: Literal["NotPlanned", "Definite"]

    def __str__(self):
        if self.type == "NotPlanned":
            return ""
        start_dt = (datetime.min + timedelta(minutes=self.start)).strftime("%H:%M")
        end_dt = (datetime.min + timedelta(minutes=self.end)).strftime("%H:%M")
        text_type = "Немає світла ❌"
        return f"{text_type} з {start_dt} до {end_dt}"


class OutagesPlan(BaseModel):
    date: datetime
    slots: list[Slot]
    status: str  # Literal["EmergencyShutdowns", "ScheduleApplies", "WaitingForSchedule", "NoOutages"]
    updated_on: datetime | None = Field(default=None, alias="updatedOn")

    def stats(self) -> DayStat | None:
        if self.slots:
            outages_minutes = sum(slot.end - slot.start for slot in self.slots if slot.type == "Definite")
            power_minutes = sum(slot.end - slot.start for slot in self.slots if slot.type == "NotPlanned")
        else:
            outages_minutes = 0
            power_minutes = 1440
        return DayStat(
            outages_minutes=outages_minutes,
            power_minutes=power_minutes,
        )

    def __str__(self):
        slots_message: str | None = None
        hours_stats_message: str | None = None
        match self.status:
            case "EmergencyShutdowns":
                return "🚨 Екстрені відключення, графіки не діють"
            case "ScheduleApplies":
                status_message = "Діють графіки запланованих відключень"
                hours_stats_message = str(self.stats())
            case "WaitingForSchedule":
                status_message = "Буде застосовуватися графік"
            case "NoOutages":
                return "Без відключень"
            case _:
                logger.warning("Unknown status: %s, full plan: %s", self.status, self)

        if self.slots:
            slots_message = "\n".join([str(slot) for slot in self.slots if str(slot)])
        else:
            slots_message = "⏳ Очікуємо оновлення"
        slots_message = "\n".join([slots_message, hours_stats_message]) if hours_stats_message else slots_message
        return "\n".join([status_message, slots_message])


class PlanInfo(BaseModel):
    updated_on: datetime = Field(alias="updatedOn")
    today: OutagesPlan
    tomorrow: OutagesPlan


class NotificationMessage(BaseModel):
    notification_type: NotificationType
    plan: OutagesPlan

    def __str__(self) -> str:
        plan_date_str = self.plan.date.strftime("%d.%m.%Y")
        match self.notification_type:
            case NotificationType.PLAN_CHANGED:
                header = f"Зміни в плані відключень на {plan_date_str}:\n"
            case NotificationType.PLAN_NEW:
                header = f"Новий план відключень на {plan_date_str}:\n"
            case NotificationType.PLAN_STABLE:
                header = f"План відключень на {plan_date_str} залишився без змін:\n"
            case _:
                header = "Невідомий тип повідомлення.\n"

        return f"{header}{str(self.plan)}"
