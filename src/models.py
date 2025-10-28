from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime, timedelta
from enum import Enum


class NotificationType(str, Enum):
    PLAN_NEW = "PlanNew"
    PLAN_CHANGED = "PlanChanged"
    PLAN_STABLE = "PlanStable"


class Slot(BaseModel):
    start: int
    end: int
    type: Literal["NotPlanned", "Definite"]

    def __str__(self):
        start_dt = (datetime.min + timedelta(minutes=self.start)).strftime("%H:%M")
        end_dt = (datetime.min + timedelta(minutes=self.end)).strftime("%H:%M")
        text_type = "Є світло 💡" if self.type == "NotPlanned" else "Немає світла ❌"
        return f"{text_type} з {start_dt} до {end_dt}"


class OutagesPlan(BaseModel):
    date: datetime
    slots: list[Slot]
    status: Literal["EmergencyShutdowns", "ScheduleApplies", "WaitingForSchedule", "NoOutages"]
    updated_on: datetime | None = Field(default=None, alias="updatedOn")

    def __str__(self):
        match self.status:
            case "EmergencyShutdowns":
                status_message = "🚨 Екстрені відключення, графіки не діють"
            case "ScheduleApplies":
                status_message = "Діють графіки запланованих відключень"
            case "WaitingForSchedule":
                status_message = "Буде застосовуватися графік"
            case "NoOutages":
                status_message = "Без відключень"
            case _:
                status_message = ""
        return "\n".join([status_message, "\n".join([str(slot) for slot in self.slots])])


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
