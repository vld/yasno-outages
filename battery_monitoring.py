import logging
from pyaml_env import parse_config
from src.config import DeyeConfig
from src.deye_api import DeyeApi
from src.factories import NotifierFactory, StorageFactory
from src.notification import NotificationDispatcher

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("YasnoOutageMonitor")

if __name__ == "__main__":
    conf_dict = parse_config("config/config.yaml")

    notifier = NotifierFactory.create_notifier(conf_dict["notifier"])
    notification_dispatcher = NotificationDispatcher(notifier=notifier)

    deye_config = DeyeConfig(**conf_dict["deye"])
    deye_api = DeyeApi(deye_config)
    station_infos = deye_api.station_long_info()
    monitoring_storage = StorageFactory.create_storage(conf_dict["monitoring_storage"])
    logger.info("Station infos: %r", station_infos)
    notification_dispatcher.station_notification(station_infos=station_infos, storage=monitoring_storage)
