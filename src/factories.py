from src.notification import BaseNotifier, TelegramNotifier, TelegramConfig, PrintNotifier
from src.config import FileStorageConfig
from src.data_tools import BaseInfoStorage, FileInfoStorage


class NotifierFactory:
    @staticmethod
    def create_notifier(config: dict) -> BaseNotifier:
        match config["type"]:
            case "print":
                notifier = PrintNotifier()
            case "telegram":
                telegram_config = TelegramConfig(**config)
                notifier = TelegramNotifier(telegram_config)
            case _:
                raise ValueError(f"Unknown notifier type: {config['type']}")
        return notifier


class StorageFactory:
    @staticmethod
    def create_storage(config: dict) -> BaseInfoStorage:
        match config["type"]:
            case "file_storage":
                config_file = FileStorageConfig(**config)
                storage = FileInfoStorage(config=config_file)  # Placeholder for file storage implementation
            case _:
                raise ValueError(f"Unknown storage type: {config['type']}")
        return storage
