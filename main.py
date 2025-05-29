import json
import os.path
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from timezonefinder import TimezoneFinder

from tools.latex import make_latex
from tools.plots import make_plots
from tools.voacap import run_voacap
from tools.voacap_extractor import extract, get_band
from tools.wspr import wsprlive_get_info, wsprlive_pull_one_month

global FROM_DATE, TO_DATE, CONFIG, SSN_DATA


def read_config():
    global FROM_DATE, TO_DATE, CONFIG, SSN_DATA

    SSN_DATA = json.load(open('data/ssn.json'))
    CONFIG = json.load(open('config.json'))
    time_period = CONFIG['time_period']

    FROM_DATE = datetime.strptime(time_period['from'] + "-01", "%Y-%m-%d").replace(tzinfo=ZoneInfo("UTC"))
    TO_DATE = datetime.strptime(time_period['to'] + "-01", "%Y-%m-%d").replace(tzinfo=ZoneInfo("UTC"))


def one_month(circuit, current_datetime):
    info = wsprlive_get_info(circuit, current_datetime)
    if not info: return

    tx_lat = info['tx_lat']
    tx_lon = info['tx_lon']
    rx_lat = info['rx_lat']
    rx_lon = info['rx_lon']

    MONTH = current_datetime.strftime("%Y %m.00")  # .00 is needed for VOACAP config
    SSN = next((item['ssn'] for item in SSN_DATA if item['time-tag'] == current_datetime.strftime("%Y-%m")))
    TX = circuit["tx"]
    RX = circuit["rx"]
    CIRCUIT = f"{abs(tx_lat):05.2f}{'N' if tx_lat >= 0 else 'S'}   {abs(tx_lon):06.2f}{'E' if tx_lon >= 0 else 'W'}    {abs(rx_lat):05.2f}{'N' if rx_lat >= 0 else 'S'}   {abs(rx_lon):06.2f}{'E' if rx_lon >= 0 else 'W'}"
    NOISE = circuit['noise']
    POWER = f"{info['power'] * 0.0008:.4f}"  # divide by 1000 and 80% efficiency, VOACAP online does that

    local_tz = TimezoneFinder().timezone_at(lat=rx_lat, lng=rx_lon)
    run_voacap(MONTH, SSN, TX, RX, CIRCUIT, NOISE, POWER)
    wsprlive_pull_one_month(TX, RX, MONTH, current_datetime, local_tz)


def prep_data():
    data_path = Path("data/data")
    if os.path.exists(data_path): shutil.rmtree(data_path)

    for circuit in CONFIG["circuits"]:
        circuit["noise"] = CONFIG["noise_levels"].get(circuit["noise"])  # Translate noise

        current_datetime = FROM_DATE
        while current_datetime <= TO_DATE:
            one_month(circuit, current_datetime)
            current_datetime += relativedelta(months=1)


def plot():
    data_path = Path("data/figures")
    if os.path.exists(data_path): shutil.rmtree(data_path)

    dirs = sorted([p for p in Path("data/data").glob("*/*") if p.is_dir()])
    for path in dirs:
        voacapx = path / "voacapx.out"
        print(f"\n Going through: {path}")
        for band in get_band(voacapx):
            print(f"\tPlotting for band: {band}")
            snr = [d["value"] for d in extract("SNR", voacapx, band=band)]
            snrup = [d["value"] for d in extract("SNR UP", voacapx, band=band)]
            snrlw = [d["value"] for d in extract("SNR LW", voacapx, band=band)]

            make_plots(path, band, snr, snrup, snrlw)


def main():
    read_config()
    #prep_data()
    plot()
    make_latex()
    print("\n Done!")


if __name__ == "__main__":
    main()
