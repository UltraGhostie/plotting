import json
import math
import os.path
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from timezonefinder import TimezoneFinder

from tools.latex import make_latex
from tools.plots import make_plots, CAPTIONS
from tools.voacap import run_voacap
from tools.voacap_extractor import extract, get_band
from tools.wspr import wsprlive_get_info, wsprlive_pull_one_month, wsprlive_get_info_group

global FROM_DATE, TO_DATE, CONFIG, SSN_DATA

ALPHA: float = 15
EARTH_LAT: float = 40007.863
EARTH_LON: float = 40075.017

DATA_POINT_PATH: Path = Path("data/data/point")
FIGURE_POINT_PATH: Path = Path("data/figures/point")

DATA_GROUP_PATH: Path = Path("data/data/group")


def _r_lat(r: float):
    return (r * 360) / EARTH_LAT


def _r_lon(r: float, rx_lat: float):
    return (r * 360) / (EARTH_LON * math.cos((rx_lat * math.pi) / 180))


def read_config():
    global FROM_DATE, TO_DATE, CONFIG, SSN_DATA

    SSN_DATA = json.load(open('data/ssn.json'))
    CONFIG = json.load(open('config.json'))
    time_period = CONFIG['time_period']

    FROM_DATE = datetime.strptime(time_period['from'] + "-01", "%Y-%m-%d").replace(tzinfo=ZoneInfo("UTC"))
    TO_DATE = datetime.strptime(time_period['to'] + "-01", "%Y-%m-%d").replace(tzinfo=ZoneInfo("UTC"))


def one_month(circuit, current_datetime):
    properties = wsprlive_get_info(circuit, current_datetime)
    if not properties: return

    tx_lat = properties['tx_lat']
    tx_lon = properties['tx_lon']
    rx_lat = properties['rx_lat']
    rx_lon = properties['rx_lon']

    MONTH = current_datetime.strftime("%Y %m.00")  # .00 is needed for VOACAP config
    SSN = next((item['ssn'] for item in SSN_DATA if item['time-tag'] == current_datetime.strftime("%Y-%m")))
    TX = circuit["tx"]
    RX = circuit["rx"]
    CIRCUIT = f"{abs(tx_lat):05.2f}{'N' if tx_lat >= 0 else 'S'}   {abs(tx_lon):06.2f}{'E' if tx_lon >= 0 else 'W'}    {abs(rx_lat):05.2f}{'N' if rx_lat >= 0 else 'S'}   {abs(rx_lon):06.2f}{'E' if rx_lon >= 0 else 'W'}"
    NOISE = circuit['noise']
    POWER = f"{properties['power'] * 0.0008:.4f}"  # divide by 1000 and 80% efficiency, VOACAP online does that

    run_voacap(MONTH, SSN, TX, RX, CIRCUIT, NOISE, POWER)
    print()

    # Point to Point
    local_tz = ZoneInfo(TimezoneFinder().timezone_at(lat=rx_lat, lng=rx_lon))
    wsprlive_pull_one_month(TX, RX, MONTH, current_datetime, local_tz, DATA_POINT_PATH)
    print(" Point pull done!\n")

    # Point to Group
    r = ALPHA * math.sqrt(properties["distance"])
    r_lat = _r_lat(r)
    r_long = _r_lon(r, rx_lat)

    path = DATA_GROUP_PATH / f"{TX}_{RX}"
    group = wsprlive_get_info_group(circuit, current_datetime, rx_lat, rx_lon, r_lat, r_long)
    for point in group:
        local_tz = ZoneInfo(TimezoneFinder().timezone_at(lat=point["rx_lat"], lng=point["rx_lon"]))
        wsprlive_pull_one_month(TX, point["rx_sign"], MONTH, current_datetime, local_tz, path)

    print(" Group pull done!\n")


def prep_data():
    if os.path.exists(DATA_POINT_PATH): shutil.rmtree(DATA_POINT_PATH)
    if os.path.exists(DATA_GROUP_PATH): shutil.rmtree(DATA_GROUP_PATH)

    for circuit in CONFIG["circuits"]:
        circuit["noise"] = CONFIG["noise_levels"].get(circuit["noise"])  # Translate noise

        current_datetime = FROM_DATE
        while current_datetime <= TO_DATE:
            one_month(circuit, current_datetime)
            current_datetime += relativedelta(months=1)


def plot():
    if os.path.exists(FIGURE_POINT_PATH): shutil.rmtree(FIGURE_POINT_PATH)

    dirs = sorted([p for p in DATA_POINT_PATH.glob("*/*") if p.is_dir()])
    for path in dirs:
        voacapx = path / "voacapx.out"
        print(f"\n Going through: {path}")
        for band in get_band(voacapx):
            print(f"\tPlotting for band: {band}")
            snr = [d["value"] for d in extract("SNR", voacapx, band=band)]
            snrup = [d["value"] for d in extract("SNR UP", voacapx, band=band)]
            snrlw = [d["value"] for d in extract("SNR LW", voacapx, band=band)]

            make_plots(path, band, snr, snrup, snrlw)
    with open(Path("data/captions.json"), "w") as file:
        json.dump(CAPTIONS, file)

def main():
    read_config()
    prep_data()
    plot()
    make_latex()

    print("\n Done!")


if __name__ == "__main__":
    main()
