from src.config import DeyeConfig
from src.models import StationShortInfo, StationLongInfo
import requests

BASE_URL = "https://eu1-developer.deyecloud.com/v1.0"
ALLOWED_SHORT_INFO_FIELDS = ("id", "name", "lastUpdateTime", "batterySOC", "gridInterconnectionType")
ALLOWED_LONG_INFO_FIELDS = (
    "generationPower",
    "consumptionPower",
    "gridPower",
    "purchasePower",
    "wirePower",
    "chargePower",
    "dischargePower",
    "batteryPower",
    "batterySOC",
    "irradiateIntensity",
)


class DeyeApi:
    def __init__(self, config: DeyeConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None

    def get_token(self) -> str:
        if not self.token:
            self.token = self.obtain_token()
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return self.token

    def _post(self, endpoint: str, json_payload: dict) -> dict:
        self.get_token()  # Ensure token is present and valid
        response = self.session.post(f"{BASE_URL}{endpoint}", json=json_payload)
        response.raise_for_status()
        return response.json()

    def obtain_token(self) -> str:
        url = f"{BASE_URL}/account/token?appId={self.config.app_id}"
        payload = {
            "email": self.config.email,
            "password": self.config.password,
            "appSecret": self.config.app_secret,
        }
        try:
            # This request should not use the session's auth header
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            raise
        except Exception as err:
            print(f"Other error occurred: {err}")
            raise
        return data["accessToken"]

    def station_list(self) -> dict:
        return self._post("/station/list", json_payload={})

    def latest_long_info(self, station_id: int) -> dict:
        return self._post("/station/latest", json_payload={"stationId": station_id})

    def station_long_info(self) -> list[StationLongInfo]:
        stations = self.station_list()
        # StationLongInfo.model_validate({k: data[k]}) for data in stations["stationList"]]:
        result_list: list[StationLongInfo] = []
        for data in stations["stationList"]:
            long_data = {
                k: val for k, val in self.latest_long_info(data["id"]).items() if k in ALLOWED_LONG_INFO_FIELDS
            }
            short_data = {k: val for k, val in data.items() if k in ALLOWED_SHORT_INFO_FIELDS}
            result_list.append(StationLongInfo.model_validate(short_data | long_data))
        return result_list

    def latest_devices_info(self, station_ids: list[int]):
        response = self._post("/station/device", json_payload={"stationIds": station_ids})
        device_sns = [
            device["deviceSn"] for device in response["deviceListItems"] if device["deviceType"] == "INVERTER"
        ]
        return self._post("/device/latest", json_payload={"deviceList": device_sns})

    def station_short_info(self) -> list[StationShortInfo]:
        devices = self.station_list()

        data_points = [
            StationShortInfo.model_validate({k: station_data[k] for k in ALLOWED_SHORT_INFO_FIELDS})
            for station_data in devices.get("stationList", [])
        ]
        return data_points
