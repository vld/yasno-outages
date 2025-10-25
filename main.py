from src.config import YasnoConfig, MySQLConfig
from src.data_tools import YasnoPlannedOutageParser, PlanDB, OutagesPlanDiffChecker
from pyaml_env import parse_config


if __name__ == "__main__":
    conf_dict = parse_config("config/config.yaml")
    yasno_config = YasnoConfig(**conf_dict["yasno"])
    yasno_parser = YasnoPlannedOutageParser(config=yasno_config)
    plan_info = yasno_parser.parse()

    config_db = MySQLConfig(**conf_dict["db"])
    plan_db = PlanDB(config=config_db)

    for parsed_plan in (plan_info.today, plan_info.tomorrow):
        date_str = parsed_plan.date.strftime("%d.%m.%Y")
        stored_plan = plan_db.read_plan(plan_date=parsed_plan.date)
        if stored_plan:
            if OutagesPlanDiffChecker.has_changes(old_plan=stored_plan, new_plan=parsed_plan):
                print(f"Plan for {date_str} has changes.")
                plan_db.save_plan(parsed_plan)
            else:
                print(f"No changes in {date_str} plan.")
        else:
            print(f"No existing plan found for {date_str}.")
            plan_db.save_plan(parsed_plan)
