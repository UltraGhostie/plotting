import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from lxml.html.builder import CAPTION

mpl.use("pgf")
plt.rcParams.update({
    "pgf.texsystem": "pdflatex",  # sudo apt install texlive-full
    "font.family": "serif",  # use LaTeX serif font
    "font.size": 11,
    "text.usetex": True,  # use LaTeX to render text
    "pgf.rcfonts": False,  # don’t override Matplotlib defaults
})

SNR_OFFSET = 34  # SNR offset to compensate for bandwidth differences between VOACAP and WSPR
HOURS = range(24)

DATA = {}
PATH = Path()

SNR_V = []
o_UP_V = []
o_LW_V = []

SNR_W: list[float] = []
o_UP_W: list[float] = []
o_LW_W: list[float] = []

DISTRO_W: list[tuple[int, list]] = []

dSNR: list[float] = []
dUP: list[float] = []
dLW: list[float] = []

CAPTIONS = {}


def prep_data():
    global DATA, SNR_W, o_UP_W, o_LW_W, DISTRO_W, dSNR, dUP, dLW

    for H in HOURS:
        snr_hour = sorted([
            entry["snr"]
            for entry
            in DATA
            if datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S").hour == H
        ])

        if len(snr_hour) >= 30:
            DISTRO_W.append((len(snr_hour), list(Counter(snr_hour).items())))

            median = float(np.percentile(snr_hour, 50))
            SNR_W.append(median)
            o_UP_W.append(abs(median - float(np.percentile(snr_hour, 90))) / 1.28)
            o_LW_W.append(abs(median - float(np.percentile(snr_hour, 10))) / 1.28)

            dSNR.append(SNR_W[H] - SNR_V[H])
            dUP.append(o_UP_W[H] - o_UP_V[H])
            dLW.append(o_LW_W[H] - o_LW_V[H])
        else:
            DISTRO_W.append((0, []))

            SNR_W.append(np.nan)
            o_UP_W.append(np.nan)
            o_LW_W.append(np.nan)

            dSNR.append(np.nan)
            dUP.append(np.nan)
            dLW.append(np.nan)


def plot_errors_bars():
    global HOURS, dSNR, dUP, dLW

    fig, ax = plt.subplots(constrained_layout=True)  # figsize=(12, 4)

    bar_width = 0.6 / 3
    x = np.arange(len(HOURS))

    ax.bar(x - bar_width, dSNR, color="#0052CC", lw=1, label=r"$\Delta\mathrm{SNR}$", width=bar_width)
    ax.bar(x, dUP, color="#CC0000", lw=1, label=r"$\Delta \sigma_\mathrm{UP}$", width=bar_width)
    ax.bar(x + bar_width, dLW, color="#2CA02C", lw=1, label=r"$\Delta \sigma_\mathrm{LW}$", width=bar_width)

    ax.set_title("Hourly VOACAP Parameter Deviations from WSPR")
    ax.set_ylabel("Deviation (dB·Hz)")
    ax.set_xlabel("Hour (Receiver Local Time)")

    ax.set_xticks(x)
    ax.margins(x=0.01, y=0.01)

    ax.legend()
    ax.minorticks_on()
    ax.grid(True, which='major', alpha=0.5)
    ax.grid(True, which='minor', alpha=0.3)

    avg_dsnr = np.nanmean(np.abs(np.array(dSNR)))
    avg_dup = np.nanmean(np.abs(np.array(dUP)))
    avg_dlw = np.nanmean(np.abs(np.array(dLW)))
    latex_caption = (
        rf"Average deviations: "
        rf"$\overline{{\Delta \mathrm{{SNR}}}} = {avg_dsnr:.2f}\,\mathrm{{dB\cdot Hz}}$, "
        rf"$\overline{{\Delta \sigma_\mathrm{{UP}}}} = {avg_dup:.2f}\,\mathrm{{dB\cdot Hz}}$, "
        rf"$\overline{{\Delta \sigma_\mathrm{{LW}}}} = {avg_dlw:.2f}\,\mathrm{{dB\cdot Hz}}$"
    )

    path = PATH / "error_bars.pdf"
    CAPTIONS[path] = latex_caption

    fig.savefig(path)
    plt.close(fig)


def plot_hour_normal_distros():
    global SNR_W, o_UP_W, o_LW_W, SNR_V, o_UP_V, o_LW_V

    for H in HOURS:
        sample_size, hour_distro = DISTRO_W[H]
        if not hour_distro: continue

        # Parameters for two split normal distributions
        EPS = 1e-16  # Dodge sigma = 0
        mu1, o_l1, o_u1 = SNR_W[H], max(o_LW_W[H], EPS), max(o_UP_W[H], EPS)
        mu2, o_l2, o_u2 = SNR_V[H], max(o_LW_V[H], EPS), max(o_UP_V[H], EPS)
        A1, A2 = np.sqrt(2 / np.pi) / (o_l1 + o_u1), np.sqrt(2 / np.pi) / (o_l2 + o_u2)

        # Generate x values over a range covering both distributions
        o_off = 4
        x = np.linspace(
            min(hour_distro[0][0], mu1 - o_off * o_u1, mu2 - o_off * o_u2),
            max(hour_distro[-1][0], mu1 + o_off * o_u1, mu2 + o_off * o_u2), 300)

        snr, count = zip(*hour_distro)
        prob = [c / sample_size for c in count]

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
        fig, ax = plt.subplots(constrained_layout=True)  # figsize=(10, 10),

        label1, = ax.plot(snr, prob, lw=1, color="#0052CC", label="WSPR")
        ax.fill_between(snr, 0, prob, alpha=0.2)
        label2, = ax.plot(x, pdf1, lw=1, color="#CC0000", label="Interpolated")
        ax.fill_between(x, 0, pdf1, alpha=0.2)
        label3, = ax.plot(x, pdf2, lw=1, color="#2CA02C", label="VOACAP")
        ax.fill_between(x, 0, pdf2, alpha=0.2)

        ax.set_title(f"SNR distribution (Hour {H})")
        ax.set_ylabel("Probability")
        ax.set_xlabel("SNR (dB·Hz)")

        ax.margins(x=0, y=0)
        ymin, ymax = ax.get_ylim()
        padding = 0.05 * (ymax - ymin)
        ax.set_ylim(ymin, ymax + padding)

        ax.legend(handles=[label1, label2, label3])
        ax.minorticks_on()
        ax.grid(True, which='major', alpha=0.5)
        ax.grid(True, which='minor', alpha=0.3)

        fig.savefig(PATH / f"normal_h{H}.pdf")
        plt.close(fig)


def make_plots(path: Path, band: int, snr: list[float], snr_up: list[float], snr_lw: list[float]):
    global DATA, CAPTIONS, SNR_V, o_UP_V, o_LW_V, SNR_W, o_UP_W, o_LW_W, DISTRO_W, dSNR, dUP, dLW, PATH

    DATA = json.load(open(path / f"{band}.json"))
    if not DATA: return

    PATH = "data/figures" / path.relative_to(path.parent.parent) / str(band)
    PATH.mkdir(parents=True, exist_ok=True)

    SNR_V = [s - SNR_OFFSET for s in snr]
    o_UP_V = [abs(up / 1.28) for up in snr_up]
    o_LW_V = [abs(lw / 1.28) for lw in snr_lw]

    SNR_W.clear()
    o_UP_W.clear()
    o_LW_W.clear()

    DISTRO_W.clear()

    dSNR.clear()
    dUP.clear()
    dLW.clear()

    prep_data()
    plot_errors_bars()
    plot_hour_normal_distros()
