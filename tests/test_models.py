from src.models import OutagesPlan, DayStat, Slot
import pytest
from pydantic import ValidationError


def test_outages_plan(raw_plan):
    correct_outages_plan = OutagesPlan(**raw_plan)
    wrong_raw_outages_plan = raw_plan | {"slots": [Slot(start=0, end=700, type="Definite")]}
    wrong_outages_plan = OutagesPlan(**wrong_raw_outages_plan)
    all_day_light = DayStat(outages_minutes=0, power_minutes=1440)
    assert correct_outages_plan.stats() == all_day_light
    with pytest.raises(ValidationError):
        wrong_outages_plan.stats() == all_day_light
