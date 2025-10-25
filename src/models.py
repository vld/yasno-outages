from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class Slot(BaseModel):
    start: int
    end: int
    type: Literal["NotPlanned", "Definite"]


class OutagesPlan(BaseModel):
    date: datetime
    slots: list[Slot]
    updated_on: datetime | None = Field(default=None, alias="updatedOn")


class PlanInfo(BaseModel):
    updated_on: datetime = Field(alias="updatedOn")
    today: OutagesPlan
    tomorrow: OutagesPlan
