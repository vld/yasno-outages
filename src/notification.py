from abc import ABC, abstractmethod
from src.data_tools import BaseInfoStorage, get_bar
from src.models import PlanNotificationMessage, OutagesPlan, NotificationType, StationLongInfo
from src.config import TelegramConfig
import requests
import logging

logger = logging.getLogger("YasnoOutageMonitor")


class BaseNotifier(ABC):
    @abstractmethod
    def send_notification(self, message: str) -> None:
        pass


class PrintNotifier(BaseNotifier):
    def send_notification(self, message: str) -> None:
        print(message)


class TelegramNotifier(BaseNotifier):
    def __init__(self, config: TelegramConfig):
        self.config = config

    def send_notification(self, message: str) -> None:
        try:
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            payload = {
                "chat_id": self.config.chat_id,
                "text": message,
                "parse_mode": "HTML",
            }
            if self.config.thread_id:
                payload["thread_id"] = self.config.thread_id
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to send Telegram message: %s. Response: %s", e, response.text)


class NotificationDispatcher:
    def __init__(self, notifier: BaseNotifier) -> None:
        self.notifier = notifier

    def plan_notification(self, plan: OutagesPlan, change_type: NotificationType) -> None:
        if plan.status in ("WaitingForSchedule", "ScheduleApplies") and not plan.slots:
            logger.info("No information to send, plan: [%r].", repr(plan))
            return
        message = PlanNotificationMessage(notification_type=change_type, plan=plan)
        self.notifier.send_notification(message=str(message))

    def station_notification(self, station_infos: list[StationLongInfo]):
        grid_disconnected = all(not station.is_grid_connected() for station in station_infos)
        if grid_disconnected:
            all_socs = [station.battery_soc for station in station_infos if station.battery_soc is not None]
            avg_soc = sum(all_socs) / len(all_socs) if all_socs else 0
            message = f"<b>Статус батарей CEC:</b>\n<code>{get_bar(avg_soc)}</code>"
            self.notifier.send_notification(message)
        else:
            logger.info("At least one station is connected to the grid.")
