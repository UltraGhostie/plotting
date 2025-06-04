import json
from datetime import datetime
from itertools import groupby
from zoneinfo import ZoneInfo

import httpx
from dateutil.relativedelta import relativedelta


# BANDS = ["0", "1", "3", "5", "7", "10", "14", "18", "21", "24", "28", "50", "70", "144", "432", "1296", "-1"]


def wsprlive_get(query, client=httpx.Client(http2=True, timeout=None)):
    url = "https://db1.wspr.live/"
    params = {"query": query + " FORMAT JSON"}

    response = client.get(url, params=params)
    response.raise_for_status()
    json_obj = response.json()

    if "exception" in json_obj: print(f" \033[91m{json_obj["exception"]}\033[0m")

    return json_obj["data"]


def wsprlive_get_info(circuit, current_datetime):
    start = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    end = (current_datetime + relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")

    json_obj = wsprlive_get(
        f"SELECT tx_lat, tx_lon, rx_lat, rx_lon, power, distance "
        f"FROM rx "
        f"WHERE tx_sign = '{circuit['tx']}' AND rx_sign = '{circuit['rx']}' "
        f"AND '{start}' <= time AND time < '{end}' "
        f"LIMIT 1")
    return json_obj[0] if json else {}


def wsprlive_get_info_group(circuit, current_datetime, c_lat: float, c_lon: float, r_lat: float, r_lon: float):
    start = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    end = (current_datetime + relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")

    return wsprlive_get(
        f"SELECT DISTINCT rx_sign, rx_lat, rx_lon, power "
        f"FROM rx "
        f"WHERE tx_sign = '{circuit['tx']}' AND rx_sign != '{circuit['rx']}' "
        f"AND abs(rx_lat - CAST({c_lat} AS Float32)) <= {r_lat} "
        f"AND abs(rx_lon - CAST({c_lon} AS Float32)) <= {r_lon} "
        f"AND '{start}' <= time AND time < '{end}'")


def wsprlive_pull_one_month(tx, rx, current_datetime, local_tz, prefix_path, suffix_path: str = ""):
    print(f" Pulling: {tx} - {rx}")

    local_datetime = current_datetime.astimezone(local_tz)
    start = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
    end = (local_datetime + relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")

    json_obj = wsprlive_get(
        f"SELECT time, band, frequency, snr, power "
        f"FROM rx "
        f"WHERE tx_sign = '{tx}' AND rx_sign = '{rx}' "
        f"AND '{start}' <= time "
        f"AND time < '{end}' "
        f"ORDER BY band, time ASC")

    utc_tz = ZoneInfo("UTC")
    for entry in json_obj:
        entry["time"] = (
            datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=local_tz)
            .astimezone(utc_tz)
            .strftime("%Y-%m-%d %H:%M:%S")
        )

    for band, group in groupby(json_obj, lambda e: e["band"]):
        full_path = prefix_path / f"{band:02d}{suffix_path}.json"
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w") as file:
            json.dump(list(group), file)
