from src.config import YasnoConfig
from src.readers import YasnoPlannedOutageParser
import yaml


if __name__ == "__main__":
    conf_dict = yaml.safe_load(open("config/config.yaml"))
    yasno_config = YasnoConfig(**conf_dict["yasno"])
    yasno_parser = YasnoPlannedOutageParser(config=yasno_config)
    plan_info = yasno_parser.parse()
    print(repr(plan_info), plan_info)
