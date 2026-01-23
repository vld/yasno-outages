from abc import ABC, abstractmethod
import logging
import requests
from src.config import TelegramConfig
from src.data_tools import BaseInfoStorage
from src.models import (
    MonitoringInfo,
    PlanNotificationMessage,
    OutagesPlan,
    NotificationType,
    StationLongInfo,
    DataPoint,
)
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger("YasnoOutageMonitor")


class BaseNotifier(ABC):
    @abstractmethod
    def send_message(self, message: str) -> None:
        pass

    @abstractmethod
    def update_message(self, message_id: int, message: str) -> None:
        pass


class PrintNotifier(BaseNotifier):
    def send_message(self, message: str) -> None:
        print(message)


class TelegramNotifier(BaseNotifier):
    def __init__(self, config: TelegramConfig):
        self.config = config

    def send_message(self, message: str) -> dict:
        try:
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            payload = {
                "chat_id": self.config.chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            if self.config.thread_id:
                payload["message_thread_id"] = self.config.thread_id
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to send Telegram message: %s. Response: %s", e, response.text)
        return response.json()

    def update_message(self, message_id: int, message: str) -> None:
        try:
            url = f"https://api.telegram.org/bot{self.config.bot_token}/editMessageText"
            payload = {
                "chat_id": self.config.chat_id,
                "message_id": message_id,
                "text": message,
                "parse_mode": "HTML",
            }
            if self.config.thread_id:
                payload["message_thread_id"] = self.config.thread_id
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to update Telegram message: %s. Response: %s", e, response.text)


class NotificationDispatcher:
    def __init__(self, notifier: BaseNotifier) -> None:
        self.notifier = notifier

    def plan_notification(self, plan: OutagesPlan, change_type: NotificationType) -> None:
        if plan.status in ("WaitingForSchedule", "ScheduleApplies") and not plan.slots:
            logger.info("No information to send, plan: [%r].", repr(plan))
            return
        message = PlanNotificationMessage(notification_type=change_type, plan=plan)
        self.notifier.send_message(message=str(message))

    def station_notification(self, station_infos: list[StationLongInfo], storage: BaseInfoStorage) -> None:
        # grid_disconnected = all(not station.is_grid_connected() for station in station_infos)
        grid_disconnected = True
        if grid_disconnected:
            datetime_now = datetime.now(tz=ZoneInfo("Europe/Kyiv"))
            all_socs = [station.battery_soc for station in station_infos if station.battery_soc is not None]
            avg_soc = sum(all_socs) / len(all_socs) if all_socs else 0
            dp = DataPoint(timestamp=datetime_now, soc=avg_soc)
            # check if we have already have daily message
            try:
                monitoring_info = storage.read(object_date=datetime_now.date(), name_prefix="monitoring")
            except Exception as e:
                logger.warning("Failed to read monitoring info: %s", e)
                monitoring_info = None
            if monitoring_info:
                monitoring_info.data_points.append(dp)
                storage.save_monitoring(monitoring_info)
                self.notifier.update_message(monitoring_info.message_id, str(monitoring_info))
            else:
                monitoring_info = MonitoringInfo(date=datetime_now.date(), data_points=[dp])
                result = self.notifier.send_message(str(monitoring_info))
                monitoring_info.message_id = result["result"]["message_id"]
                storage.save_monitoring(monitoring_info)
        else:
            logger.info("At least one station is connected to the grid.")
