from pydantic import BaseModel


class YasnoConfig(BaseModel):
    city_id: int
    dso_id: int
    group_id: str
    local_tz: str
    url: str
