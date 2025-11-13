from abc import ABC, abstractmethod
from src.models import NotificationMessage, OutagesPlan, NotificationType
from src.config import TelegramConfig
import requests
import logging

logger = logging.getLogger("YasnoOutageMonitor")


class BaseNotifier(ABC):
    @abstractmethod
    def send_notification(self, message: NotificationMessage) -> None:
        pass


class PrintNotifier(BaseNotifier):
    def send_notification(self, message: NotificationMessage) -> None:
        print(message)


class TelegramNotifier(BaseNotifier):
    def __init__(self, config: TelegramConfig):
        self.config = config

    def send_notification(self, message: NotificationMessage) -> None:
        try:
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            payload = {"message_thread_id": self.config.thread_id, "chat_id": self.config.chat_id, "text": str(message)}
            response = requests.post(url, data=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to send Telegram message: %s. Response: %s", e, response.text)


class NotificationDispatcher:
    def __init__(self, notifier: BaseNotifier) -> None:
        self.notifier = notifier

    def check_and_notify(self, plan: OutagesPlan, change_type: NotificationType) -> None:
        if plan.status in ("WaitingForSchedule", "ScheduleApplies") and not plan.slots:
            logger.info("No information to send, plan: [%r].", repr(plan))
            return
        message = NotificationMessage(notification_type=change_type, plan=plan)
        self.notifier.send_notification(message=message)
