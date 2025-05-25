import urllib.request
import json
from pathlib import Path

from dateutil.relativedelta import relativedelta

bands = ["-1", "0", "1", "3", "5", "7", "10", "14", "18", "21", "24", "28", "50", "70", "144", "432", "1296"]


def wsprlive_get(query):
    url = "https://db1.wspr.live/?query=" + urllib.parse.quote_plus(query + " FORMAT JSON")
    contents = urllib.request.urlopen(url).read()
    return json.loads(contents.decode("UTF-8"))["data"]


def wsprlive_get_info(circuit, current_date):
    return wsprlive_get(
        f"SELECT tx_lat, tx_lon, rx_lat, rx_lon, power FROM rx WHERE tx_sign = '{circuit['tx']}' AND rx_sign = '{circuit['rx']}' AND '{current_date}' <= time AND time < '{current_date + relativedelta(months=1)}' LIMIT 1")[0]


def wsprlive_pull_one_month(TX, RX, MONTH, current_date):
    global bands

    path = Path("data") / "wspr" / f"{TX}_{RX}"
    path.mkdir(parents=True, exist_ok=True)

    for band in bands:
        band_path = path / band
        band_path.mkdir(parents=True, exist_ok=True)

        json_obj = wsprlive_get(
            f"SELECT time, band, frequency, snr, power FROM rx WHERE band = '{band}' AND tx_sign = '{TX}' AND rx_sign = '{RX}' AND '{current_date}' <= time AND time < '{current_date + relativedelta(months=1)}' ORDER BY time ASC")
        with open(band_path / f"{MONTH.replace(" ", "_")}.json", "w") as file:
            json.dump(json_obj, file)
