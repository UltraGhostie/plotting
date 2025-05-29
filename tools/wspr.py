import json
import urllib.request
import urllib.parse

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta

BANDS = ["-1", "0", "1", "3", "5", "7", "10", "14", "18", "21", "24", "28", "50", "70", "144", "432", "1296"]


def wsprlive_get(query):
    url = "https://db1.wspr.live/?query=" + urllib.parse.quote_plus(query + " FORMAT JSON")
    contents = urllib.request.urlopen(url).read()
    return json.loads(contents.decode("UTF-8"))["data"]


def wsprlive_get_info(circuit, current_datetime):
    start = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    end = (current_datetime + relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")

    json  = wsprlive_get(
        f"SELECT tx_lat, tx_lon, rx_lat, rx_lon, power "
        f"FROM rx "
        f"WHERE tx_sign = '{circuit['tx']}' AND rx_sign = '{circuit['rx']}' "
        f"AND '{start}' <= time "
        f"AND time < '{end}' "
        f"LIMIT 1")
    return json[0] if json else {}


def wsprlive_pull_one_month(tx, rx, month, current_datetime, local_tz):
    global BANDS

    path = Path("data") / "data" / f"{tx}_{rx}"
    path.mkdir(parents=True, exist_ok=True)

    current_datetime = current_datetime.astimezone(ZoneInfo(local_tz))
    start = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    end = (current_datetime + relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")

    for band in BANDS:
        date_path = path / f"{month.replace(" ", "_")}"
        date_path.mkdir(parents=True, exist_ok=True)

        json_obj = wsprlive_get(
            f"SELECT time, band, frequency, snr, power "
            f"FROM rx "
            f"WHERE band = '{band}' "
            f"AND tx_sign = '{tx}' AND rx_sign = '{rx}' "
            f"AND '{start}' <= time "
            f"AND time < '{end}' "
            f"ORDER BY time ASC")

        for entry in json_obj:
            entry["time"] = (((datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
                               .replace(tzinfo=ZoneInfo(local_tz)))
                              .astimezone(ZoneInfo("UTC")))
                             .strftime("%Y-%m-%d %H:%M:%S"))

        with open(date_path / f"{band}.json", "w") as file:
            json.dump(json_obj, file)
