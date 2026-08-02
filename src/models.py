from pydantic import BaseModel, Field, model_validator
from typing import Literal
from typing_extensions import Self
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from enum import Enum
import logging

logger = logging.getLogger("YasnoOutageMonitor")
GridInterconnectionType = Literal[
    "DISTRIBUTED_FULLY",
    "EXCESS",
    "OFF_GRID",
    "BATTERY_BACKUP",
    "GROUND_FULLY",
    "CENTRALIZED_FULLY",
    "GEN_USE_BTR",
    "GEN_USE",
    "GRID_USE_BTR",
    "USE_BTR",
]


def get_bar(percent, length=15):
    """
    Створює ASCII прогрес-бар.
    percent: інцидент від 0 до 100
    length: довжина повзунка в символах
    """
    percent = max(0, min(100, percent))  # Обмежуємо від 0 до 100
    filled_length = round(length * percent // 100)

    # Використовуємо блоки: █ (повний) та ░ (пустий)
    bar = "█" * filled_length + "░" * (length - filled_length)

    return bar


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
                return "💡 Без відключень"
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


class PlanNotificationMessage(BaseModel):
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


class StationShortInfo(BaseModel):
    station_id: int = Field(alias="id")
    station_name: str = Field(alias="name")
    battery_soc: float = Field(alias="batterySOC")
    grid_interconnection_type: GridInterconnectionType = Field(alias="gridInterconnectionType")
    last_update_time: datetime = Field(alias="lastUpdateTime")


class StationLongInfo(StationShortInfo):
    generation_power: float = Field(alias="generationPower")
    consumption_power: float = Field(alias="consumptionPower")
    grid_power: float | None = Field(alias="gridPower")
    purchase_power: float | None = Field(alias="purchasePower")
    wire_power: float | None = Field(alias="wirePower")
    charge_power: float | None = Field(alias="chargePower")
    discharge_power: float | None = Field(alias="dischargePower")
    battery_power: float | None = Field(alias="batteryPower")
    battery_soc: float | None = Field(alias="batterySOC")
    irradiate_intensity: float | None = Field(alias="irradiateIntensity")

    def is_grid_connected(self) -> bool:
        return self.wire_power is not None and self.wire_power > 0


class DataPoint(BaseModel):
    timestamp: datetime
    soc: float | None = None


class MonitoringInfo(BaseModel):
    message_id: int | None = None
    date: datetime = datetime.now(tz=ZoneInfo("Europe/Kyiv"))
    data_points: list[DataPoint]

    def __str__(self) -> str:
        lines = [f"<b>Моніторинг стану батарей за {self.date.strftime('%d.%m.%Y')}:</b>"]
        for dp in self.data_points:
            time_str = dp.timestamp.strftime("%H:%M")
            lines.append(f"<code>{time_str} |{get_bar(dp.soc)}| {dp.soc:.1f}%</code>")

        return "\n".join(lines)
