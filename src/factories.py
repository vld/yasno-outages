from src.notification import BaseNotifier, TelegramNotifier, TelegramConfig, PrintNotifier
from src.config import MySQLConfig, FileStorageConfig
from src.data_tools import BaseInfoStorage, MariaDBInfoStorage, FileInfoStorage


class NotifierFactory:
    @staticmethod
    def create_notifier(config: dict) -> BaseNotifier | None:
        match config["type"]:
            case "print":
                return PrintNotifier()
            case "telegram":
                telegram_config = TelegramConfig(bot_token=config["bot_token"], chat_id=config["chat_id"])
                return TelegramNotifier(telegram_config)
            case _:
                return None


class StorageFactory:
    @staticmethod
    def create_storage(config: dict) -> BaseInfoStorage | None:
        match config["type"]:
            case "maria_db":
                config_db = MySQLConfig(**config)
                storage = MariaDBInfoStorage(config=config_db)
            case "file_storage":
                config_file = FileStorageConfig(**config)
                storage = FileInfoStorage(config=config_file)  # Placeholder for file storage implementation
            case _:
                storage = None
        return storage
