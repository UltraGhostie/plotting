import json

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import psycopg2
import scipy.stats as stats
import statistics
import math
import argparse
from datetime import datetime
from collections import Counter

parser = argparse.ArgumentParser("WSPRcomp")
_ = parser.add_argument("band", help="The band that will be fetched")
_ = parser.add_argument("predsnrs", help="Expected SNR values")
_ = parser.add_argument("predsnrups", help="Expected SNRup values")
_ = parser.add_argument("predsnrlws", help="Expected SNRlw values")
_ = parser.add_argument("sender", help="The sender in the circuit")
_ = parser.add_argument("receiver", help="The receiver in the circuit")
args = parser.parse_args()

SNR_OFFSET = 34  # SNR offset to compensate for bandwidth differences between VOACAP and WSPR
HOURS = range(24)
BAND = args.band

SNR_V = [float(snr) - SNR_OFFSET for snr in args.predsnrs.split()]
o_UP_V = [abs(float(up) / 1.28) for up in args.predsnrups.split()]
o_LW_V = [abs(float(lw) / 1.28) for lw in args.predsnrlws.split()]

SNR_W: list[float] = []
o_UP_W: list[float] = []
o_LW_W: list[float] = []

DIST_W: list[tuple[int, list]] = []

dSNR: list[float] = []
dUP: list[float] = []
dLW: list[float] = []

LABELS: list[str] = []
COLORS: list[str] = []


def something():
    global SNR_W, o_UP_W, o_LW_W, DIST_W, SIZE_W, dSNR, dUP, dLW
    data = json.load(open("/home/pavel/IdeaProjects/plotting/data/wspr/WW0WWV_EA8BFK/10/2025_01.00.json"))
    for H in HOURS:
        snr_hour = sorted([
            entry["snr"]
            for entry
            in data
            if datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S").hour == H
        ])
        DIST_W.append((snr_hour.__len__(), list(Counter(snr_hour).items())))
        LABELS.append(str(H))

        if snr_hour:
            median = float(np.percentile(snr_hour, 50))
            SNR_W.append(median)
            o_UP_W.append(abs(median - float(np.percentile(snr_hour, 90))) / 1.28)
            o_LW_W.append(abs(median - float(np.percentile(snr_hour, 10))) / 1.28)

            dSNR.append(SNR_W[H] - SNR_V[H])
            dUP.append(o_UP_W[H] - o_UP_V[H])
            dLW.append(o_LW_W[H] - o_LW_V[H])
            COLORS.append("tab:blue")
        else:
            SNR_W.append(np.nan)
            o_UP_W.append(np.nan)
            o_LW_W.append(np.nan)

            dSNR.append(np.nan)
            dUP.append(np.nan)
            dLW.append(np.nan)
            COLORS.append("tab:red")


def some():
    global BAND, HOURS, dSNR, dUP, dLW, LABELS, COLORS

    fig, (ax, axup, axlw) = plt.subplots(3, 1)
    ax.bar(HOURS, dSNR, label=LABELS, color=COLORS)
    ax.set_title("SNR Error in band " + str(BAND))
    ax.set_ylabel("Error")
    ax.set_xlabel("Hour")

    axup.bar(HOURS, dUP, label=LABELS, color=COLORS)
    axup.set_title("Sigmaup Error in band " + str(BAND))
    axup.set_ylabel("Error")
    axup.set_xlabel("Hour")

    axlw.bar(HOURS, dLW, label=LABELS, color=COLORS)
    axlw.set_title("Sigmalw Error in band " + str(BAND))
    axlw.set_ylabel("Error")
    axlw.set_xlabel("Hour")

    plt.show()


def other():
    mpl.use("pgf")
    mpl.rcParams.update({
        "pgf.texsystem": "pdflatex",          # sudo apt install texlive-full
        "font.family": "serif",              # use LaTeX serif font
        "font.size" : 11,
        "text.usetex": True,                 # use LaTeX to render text
        "pgf.rcfonts": False,                # don’t override Matplotlib defaults
    })


    # Parameters for two split normal distributions
    mu1, o_l1, o_u1 = SNR_W[0], o_LW_W[0], o_UP_W[0]
    mu2, o_l2, o_u2 = SNR_V[0], o_LW_V[0], o_UP_V[0]
    A1, A2 = np.sqrt(2 / np.pi) / (o_l1 + o_u1), np.sqrt(2 / np.pi) / (o_l2 + o_u2)

    # Generate x values over a range covering both distributions
    x = np.linspace(
        min(DIST_W[0][1][0][0], mu1 - 4 * o_u1, mu2 - 4 * o_u2),
        max(DIST_W[0][1][DIST_W[0][1].__len__()-1][0],
            mu1 + 4 * o_u1, mu2 + 4 * o_u2), 1000)

    size = DIST_W[0][0]
    snr, count = zip(*DIST_W[0][1])
    prob = [c / size for c in count]

    # Compute piecewise PDFs
    pdf1 = np.where(
        x < mu1,
        A1 * np.exp(-(((x - mu1) ** 2) / (2 * o_l1 ** 2))),
        A1 * np.exp(-(((x - mu1) ** 2) / (2 * o_u1 ** 2)))
    )
    pdf2 = np.where(
        x < mu2,
        A2 * np.exp(-(((x - mu2) ** 2) / (2 * o_l2 ** 2))),
        A2 * np.exp(-(((x - mu2) ** 2) / (2 * o_u2 ** 2)))
    )

    # Plot both on the same axes
    fig = plt.figure(figsize=(8, 5))

    label1, = plt.plot(snr, prob, lw=1, color="#0052CC", label="DATA")
    plt.fill_between(snr, 0, prob, alpha=0.3)

    label2, = plt.plot(x, pdf1, lw=1,  color="#CC0000",label="WSPR")
    plt.fill_between(x, 0, pdf1, alpha=0.3)

    label3, = plt.plot(x, pdf2, lw=1,  color="#2CA02C",label="VOACAP")
    plt.fill_between(x, 0, pdf2, alpha=0.3)


    plt.legend(handles=[label1, label2, label3])

    plt.margins(x=0)
    plt.margins(y=0.05)

    plt.title("Two Split Normal Distributions")
    plt.xlabel("x")
    plt.ylabel("Probability Density")
    plt.grid(True)

    fig.tight_layout()
    fig.savefig("/home/pavel/IdeaProjects/plotting/data/test_fig.pgf")
    #plt.show()


if __name__ == "__main__":
    something()
    # some()
    other()
