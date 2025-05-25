import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from wspr import wsprlive_get_info, wsprlive_pull_one_month
from voacap import run_voacap

global FROM_DATE, TO_DATE, CONFIG, SSN_DATA


def read_config():
    global FROM_DATE, TO_DATE, CONFIG, SSN_DATA

    SSN_DATA = json.load(open('data/ssn.json'))
    CONFIG = json.load(open('config.json'))
    time_period = CONFIG['time_period']

    FROM_DATE = datetime.strptime(time_period['from'] + "-01", "%Y-%m-%d").date()
    TO_DATE = datetime.strptime(time_period['to'] + "-01", "%Y-%m-%d").date()


def one_month(circuit, current_date):
    info = wsprlive_get_info(circuit, current_date)
    tx_lat = info['tx_lat']
    tx_lon = info['tx_lon']
    rx_lat = info['rx_lat']
    rx_lon = info['rx_lon']

    MONTH = current_date.strftime("%Y %m.00")   #.00 is needed for VOACAP config
    SSN = next((item['ssn'] for item in SSN_DATA if item['time-tag'] == current_date.strftime("%Y-%m")))
    TX = circuit["tx"]
    RX = circuit["rx"]
    CIRCUIT = f"{abs(tx_lat):05.2f}{'N' if tx_lat >= 0 else 'S'}   {abs(tx_lon):06.2f}{'E' if tx_lon >= 0 else 'W'}    {abs(rx_lat):05.2f}{'N' if rx_lat >= 0 else 'S'}   {abs(rx_lon):06.2f}{'E' if rx_lon >= 0 else 'W'}"
    NOISE = circuit['noise']
    POWER = f"{info['power'] * 0.0008:.4f}"  # divide by 1000 and 80% efficiency, VOACAP online does that

    run_voacap(MONTH, SSN, TX, RX, CIRCUIT, NOISE, POWER)
    wsprlive_pull_one_month(TX, RX, MONTH, current_date)


def main():
    read_config()

    for circuit in CONFIG["circuits"]:
        circuit["noise"] = CONFIG["noise_levels"].get(circuit["noise"])  # Translate noise

        current_date = FROM_DATE
        while current_date <= TO_DATE:
            one_month(circuit, current_date)
            current_date += relativedelta(months=1)


if __name__ == "__main__":
    main()
