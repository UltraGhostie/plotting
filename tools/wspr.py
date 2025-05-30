import json
import httpx
import asyncio
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from dateutil.relativedelta import relativedelta

BANDS = ["-1", "0", "1", "3", "5", "7", "10", "14", "18", "21", "24", "28", "50", "70", "144", "432", "1296"]


def wsprlive_get(query, client=httpx.Client(http2=True, timeout=None)):
    url = "https://db1.wspr.live/"
    params = {"query": query + " FORMAT JSON"}

    response = client.get(url, params=params)
    response.raise_for_status()
    json_obj = response.json()

    return json_obj["data"]


async def wsprlive_get_async(query, client=httpx.AsyncClient(http2=True, timeout=None)):
    url = "https://db1.wspr.live/"
    params = {"query": query + " FORMAT JSON"}

    response = await client.get(url, params=params)
    response.raise_for_status()
    json_obj = response.json()

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
        f"SELECT DISTINCT rx_sign, rx_lat, rx_lon "
        f"FROM rx "
        f"WHERE tx_sign = '{circuit['tx']}' AND rx_sign != '{circuit['rx']}' "
        f"AND abs(rx_lat - CAST({c_lat} AS Float32)) <= {r_lat} "
        f"AND abs(rx_lon - CAST({c_lon} AS Float32)) <= {r_lon} "
        f"AND '{start}' <= time AND time < '{end}'")


async def download_band_data_async(band, tx, rx, start, end, local_tz, path, cl):
    json_obj = await wsprlive_get_async(
        f"SELECT time, band, frequency, snr, power "
        f"FROM rx "
        f"WHERE band = '{band}' "
        f"AND tx_sign = '{tx}' AND rx_sign = '{rx}' "
        f"AND '{start}' <= time "
        f"AND time < '{end}' "
        f"ORDER BY time ASC", client=cl)

    for entry in json_obj:
        entry["time"] = (((datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S")
                           .replace(tzinfo=ZoneInfo(local_tz)))
                          .astimezone(ZoneInfo("UTC")))
                         .strftime("%Y-%m-%d %H:%M:%S"))

    with open(path / f"{band}.json", "w") as file:
        json.dump(json_obj, file)


async def wsprlive_pull_one_month_async(tx, rx, month, current_datetime, local_tz, path):
    print(f" Pulling: {tx} - {rx}")
    path = path / f"{tx.replace("/", "%")}_{rx.replace("/", "%")}" / f"{month.replace(" ", "_")}"
    path.mkdir(parents=True, exist_ok=True)

    local_datetime = current_datetime.astimezone(ZoneInfo(local_tz))
    start = local_datetime.strftime("%Y-%m-%d %H:%M:%S")
    end = (local_datetime + relativedelta(months=1)).strftime("%Y-%m-%d %H:%M:%S")

    async with httpx.AsyncClient(http2=True, timeout=None) as client:
        tasks = [download_band_data_async(band, tx, rx, start, end, local_tz, path, client) for band in BANDS]
        await asyncio.gather(*tasks)


def wsprlive_pull_one_month(tx, rx, month, current_datetime, local_tz, path):
    asyncio.run(wsprlive_pull_one_month_async(tx, rx, month, current_datetime, local_tz, path))
