from pytest import fixture


@fixture
def base_plan():
    plan = {"date": "2025-10-28T00:00:00+02:00", "slots": [], "updated_on": "2025-10-28T12:55:08+00:00"}
    return plan


@fixture
def slots_data():
    return [
        {"start": 0, "end": 600, "type": "NotPlanned"},
        {"start": 600, "end": 780, "type": "Definite"},
        {"start": 780, "end": 1290, "type": "NotPlanned"},
        {"start": 1290, "end": 1440, "type": "Definite"},
    ]
