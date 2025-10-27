from pydantic import BaseModel


class YasnoConfig(BaseModel):
    city_id: int
    dso_id: int
    group_id: str
    local_tz: str
    url: str


class MySQLConfig(BaseModel):
    user: str
    password: str
    host: str
    port: int
    database: str


class FileStorageConfig(BaseModel):
    path: str


class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str
