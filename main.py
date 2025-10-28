import logging
import sys
from pyaml_env import parse_config
from src.config import YasnoConfig
from src.models import NotificationType, NotificationMessage
from src.data_tools import YasnoPlannedOutageParser, OutagesPlanDiffChecker
from src.factories import NotifierFactory, StorageFactory


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

    notifier = NotifierFactory.create_notifier(conf_dict["notifier"])
    storage = StorageFactory.create_storage(conf_dict["storage"])
    if storage is None:
        logger.error("No valid storage configured.")
        sys.exit(1)

    for parsed_plan in (plan_info.today, plan_info.tomorrow):
        parsed_plan.updated_on = plan_info.updated_on
        stored_plan = storage.read_plan(plan_date=parsed_plan.date)
        message: NotificationMessage | None = None
        if stored_plan:
            if OutagesPlanDiffChecker.has_changes(old_plan=stored_plan, new_plan=parsed_plan):
                logger.info("Plan has changed %r.", parsed_plan)
                message = NotificationMessage(
                    notification_type=NotificationType.PLAN_CHANGED,
                    plan=parsed_plan,
                )
                storage.save_plan(parsed_plan)
            else:
                logger.info("No changes in plan: %r", parsed_plan)
        else:
            logger.info(
                "No existing plan found for %s, new plan: %r", parsed_plan.date.strftime("%d.%m.%Y"), parsed_plan
            )
            message = NotificationMessage(
                notification_type=NotificationType.PLAN_NEW,
                plan=parsed_plan,
            )
            storage.save_plan(parsed_plan)
        if message and notifier:
            notifier.send_notification(message=message)
