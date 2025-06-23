import json
import math
import os.path
import shutil

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from timezonefinder import TimezoneFinder

from tools.wspr import wsprlive_get_info, wsprlive_pull_one_month, wsprlive_get_info_group, wsprlive_get
from tools.voacap import run_voacap
from tools.voacap_extractor import extract
from tools.plots import make_point_plots, CAPTIONS, make_group_plots  # , magic
from tools.latex import gen_latex

global FROM_DATE, TO_DATE, CONFIG, SSN_DATA

ALPHA: float = 100
EARTH_LAT: float = 40007.863
EARTH_LON: float = 40075.017

DATA_TEMP_PATH: Path = Path("data/data/temp")
DATA_POINT_PATH: Path = Path("data/data/point")
DATA_GROUP_PATH: Path = Path("data/data/group")

FIGURE_POINT_PATH: Path = Path("data/figures/point")
FIGURE_GROUP_PATH: Path = Path("data/figures/group")


def _r_lat(r: float):
    return (r * 360) / EARTH_LAT


def _r_lon(r: float, rx_lat: float):
    return (r * 360) / (EARTH_LON * math.cos(math.radians(rx_lat)))


def dbw_to_watt(dbw):
    return 10 ** (dbw / 10) / 1000


def haversine(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Earth avg radius = 6371 km
    return 6371 * c


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
    TX, _TX = circuit["tx"], circuit["tx"].replace("/", "∕")
    RX, _RX = circuit["rx"], circuit["rx"].replace("/", "∕")
    CIRCUIT = f"{abs(tx_lat):05.2f}{'N' if tx_lat >= 0 else 'S'}   {abs(tx_lon):06.2f}{'E' if tx_lon >= 0 else 'W'}    {abs(rx_lat):05.2f}{'N' if rx_lat >= 0 else 'S'}   {abs(rx_lon):06.2f}{'E' if rx_lon >= 0 else 'W'}"
    NOISE = circuit['noise']
    PW = f"{dbw_to_watt(properties['power']) * 0.8:.4f}"  # 80% efficiency, VOACAP online does that

    run_voacap(MONTH, SSN, _TX, _RX, CIRCUIT, NOISE, PW)
    print()

    sub_path = f"{_TX}_{_RX}/{MONTH.replace(" ", "_")}"

    temp_path = DATA_TEMP_PATH / sub_path
    temp_path.mkdir(parents=True, exist_ok=True)
    file_path = temp_path / "TEMP.json"
    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("DIST", {})
    data.setdefault("POWER", {})[f"{_TX}_{_RX}"] = properties['power']

    # Point to Point
    prefix_path = DATA_POINT_PATH / sub_path
    local_tz = ZoneInfo(TimezoneFinder().timezone_at(lat=rx_lat, lng=rx_lon))
    wsprlive_pull_one_month(TX, RX, current_datetime, local_tz, prefix_path)

    print(" Point pull done!\n")

    # Point to Group
    r = ALPHA  # * math.sqrt(properties["distance"])
    r_lat = _r_lat(r)
    r_long = _r_lon(r, rx_lat)

    prefix_path = DATA_GROUP_PATH / sub_path
    group = wsprlive_get_info_group(circuit, current_datetime, rx_lat, rx_lon, r_lat, r_long)
    for point in group:
        _rx = point["rx_sign"].replace("/", "∕")
        data["DIST"][f"{_RX}_{_rx}"] = haversine(rx_lat, rx_lon, point["rx_lat"], point["rx_lon"])
        data["POWER"][f"{_TX}_{_rx}"] = point['power']

        suffix_path = f"/{_TX}_{_rx}"
        local_tz = ZoneInfo(TimezoneFinder().timezone_at(lat=point["rx_lat"], lng=point["rx_lon"]))
        wsprlive_pull_one_month(TX, point["rx_sign"], current_datetime, local_tz, prefix_path, suffix_path)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
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


def plot_point():
    if os.path.exists(FIGURE_POINT_PATH): shutil.rmtree(FIGURE_POINT_PATH)

    print("\n Plotting for point...")
    dirs = sorted([p for p in DATA_POINT_PATH.glob("*/*") if p.is_dir()])
    for path in dirs:
        voacapx = path / "voacapx.out"
        print(f" Going through: {path}")

        bands = sorted(path.glob("*.json"))
        for band_path in bands:
            band = int(band_path.stem)
            print(f"\tPlotting for band: {band}")

            snr = [d["value"] for d in extract("SNR", voacapx, band=band)]
            snrup = [d["value"] for d in extract("SNR UP", voacapx, band=band)]
            snrlw = [d["value"] for d in extract("SNR LW", voacapx, band=band)]
            rel = [d["value"] for d in extract("REL", voacapx, band=band)]

            # Compensate for 1-24 hour to 00:00-23:00 hour conversion
            snr = [snr[-1]] + snr[:-1]
            snrup = [snrup[-1]] + snrup[:-1]
            snrlw = [snrlw[-1]] + snrlw[:-1]
            rel = [rel[-1]] + rel[:-1]

            make_point_plots(path, f"{band:02d}", snr, snrup, snrlw, rel)
        print()
    with open(Path("data/captions.json"), "w") as file:
        json.dump(CAPTIONS, file, indent=2)
    # magic()


def plot_group():
    if os.path.exists(FIGURE_GROUP_PATH): shutil.rmtree(FIGURE_GROUP_PATH)

    print("\n Plotting for group...")
    dirs = sorted([p for p in DATA_GROUP_PATH.glob("*/*") if p.is_dir()])
    for path in dirs:
        print(f" Going through: {path}")
        bands = sorted(path.glob("*"))
        for band_path in bands:
            print(f"\tPlotting for band: {int(band_path.name)}")
            make_group_plots(path, band_path.name)
        print()
    with open(Path("data/captions.json"), "w") as file:
        json.dump(CAPTIONS, file, indent=2)


def main():
    read_config()
    prep_data()
    plot_point()
    plot_group()
    gen_latex()

    print(" Done!")


if __name__ == "__main__":
    main()
