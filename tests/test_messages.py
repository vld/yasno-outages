from src.models import OutagesPlan, Slot
from datetime import datetime, timedelta


def test_messages():
    plan_base = {"date": "2025-10-28T00:00:00+02:00", "slots": [], "updated_on": "2025-10-28T12:55:08+00:00"}
    expected_messages = [
        "🚨 Екстрені відключення, графіки не діють",
        "Діють графіки запланованих відключень\n⏳ Очікуємо оновлення",
        "Буде застосовуватися графік\n⏳ Очікуємо оновлення",
        "Без відключень",
    ]
    for ind, status in enumerate(["EmergencyShutdowns", "ScheduleApplies", "WaitingForSchedule", "NoOutages"]):
        plan_dict = plan_base | {"status": status}
        plan = OutagesPlan(**plan_dict)
        assert str(plan) == expected_messages[ind]
