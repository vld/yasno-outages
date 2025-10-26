from src.config import YasnoConfig, MySQLConfig, TelegramConfig
from src.models import NotificationType, NotificationMessage
from src.data_tools import YasnoPlannedOutageParser, PlanDB, OutagesPlanDiffChecker
from src.notification import PrintNotifier, TelegramNotifier
from pyaml_env import parse_config
import logging


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("YasnoOutageMonitor")


if __name__ == "__main__":
    conf_dict = parse_config("config/config.yaml")
    yasno_config = YasnoConfig(**conf_dict["yasno"])
    yasno_parser = YasnoPlannedOutageParser(config=yasno_config)
    plan_info = yasno_parser.parse()

    config_db = MySQLConfig(**conf_dict["db"])
    plan_db = PlanDB(config=config_db)

    telegram_conf = TelegramConfig(**conf_dict["notifier"])
    notifier = TelegramNotifier(telegram_conf)
    for parsed_plan in (plan_info.today, plan_info.tomorrow):
        date_str = parsed_plan.date.strftime("%d.%m.%Y")
        stored_plan = plan_db.read_plan(plan_date=parsed_plan.date)
        message: NotificationMessage | None = None
        if stored_plan:
            if OutagesPlanDiffChecker.has_changes(old_plan=stored_plan, new_plan=parsed_plan):
                logger.info("Plan has changed %s.", parsed_plan)
                message = NotificationMessage(
                    notification_type=NotificationType.PLAN_CHANGED,
                    plan=parsed_plan,
                )
                plan_db.save_plan(parsed_plan)
            else:
                logger.info("No changes in %s plan.", date_str)
        else:
            logger.info("No existing plan found for %s.", date_str)
            message = NotificationMessage(
                notification_type=NotificationType.PLAN_NEW,
                plan=parsed_plan,
            )
            plan_db.save_plan(parsed_plan)
        if message:
            notifier.send_notification(message=message)
