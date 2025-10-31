from src.models import OutagesPlan, Slot


def test_empty_slots_messages(base_plan):
    expected_messages = [
        "🚨 Екстрені відключення, графіки не діють",
        "Діють графіки запланованих відключень\n⏳ Очікуємо оновлення",
        "Буде застосовуватися графік\n⏳ Очікуємо оновлення",
        "Без відключень",
    ]
    for ind, status in enumerate(["EmergencyShutdowns", "ScheduleApplies", "WaitingForSchedule", "NoOutages"]):
        plan_dict = base_plan | {"status": status}
        plan = OutagesPlan(**plan_dict)
        assert str(plan) == expected_messages[ind]


def test_slots_messages(base_plan, slots_data):
    slots = [Slot(**d) for d in slots_data]
    expected_messages = [
        "🚨 Екстрені відключення, графіки не діють",
        "Діють графіки запланованих відключень\nНемає світла ❌ з 10:00 до 13:00\nНемає світла ❌ з 21:30 до 00:00",
        "Буде застосовуватися графік\nНемає світла ❌ з 10:00 до 13:00\nНемає світла ❌ з 21:30 до 00:00",
        "Без відключень",
    ]
    for ind, status in enumerate(["EmergencyShutdowns", "ScheduleApplies", "WaitingForSchedule", "NoOutages"]):
        plan_dict = base_plan | {"status": status, "slots": slots}
        plan = OutagesPlan(**plan_dict)
        assert str(plan) == expected_messages[ind]
