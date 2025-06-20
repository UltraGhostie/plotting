import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

mpl.use("pgf")
plt.rcParams.update({
    "pgf.texsystem": "pdflatex",  # sudo apt install texlive-full
    "font.family": "serif",  # use LaTeX serif font
    "font.size": 11,
    "text.usetex": True,  # use LaTeX to render text
    "pgf.rcfonts": False,  # don’t override Matplotlib defaults
})

SNR_OFFSET = 34  # SNR offset to compensate for bandwidth differences between VOACAP and WSPR
REQ_SNR = 3 - SNR_OFFSET
HOURS = range(24)

FIGURE_POINT_PATH: Path = Path("data/figures/point")
FIGURE_GROUP_PATH: Path = Path("data/figures/group")

WSPR_NORM: dict[str, dict[str, list]] = {}
POWER: dict[str, float] = {}
CAPTIONS = {}


def get_per_hour_distros(path: Path):
    data = json.load(open(path))

    normal: list[dict[str, float]] = []
    distro: list[dict[str, list[float] | int]] = []
    req_snr: list[float] = []
    rel: list[float] = []

    for H in HOURS:
        snr_hour = sorted([
            entry["snr"]
            for entry
            in data
            if datetime.strptime(entry["time"], "%Y-%m-%d %H:%M:%S").hour == H
        ])
        size = len(snr_hour)

        if size >= 1:
            median = float(np.percentile(snr_hour, 50))
            o_up = abs(median - float(np.percentile(snr_hour, 90))) / 1.28
            o_lw = abs(median - float(np.percentile(snr_hour, 10))) / 1.28
            normal.append({"snr": median, "up": o_up, "lw": o_lw})

            snr, count = zip(*Counter(snr_hour).items())
            distro.append({"snr": list(snr), "p": [c / size for c in count], "size": size})

            req_snr.append(float(np.percentile(snr_hour, 1)))
            rel.append(sum(1 for snr in snr_hour if snr >= REQ_SNR) / size)
        else:
            normal.append({"snr": np.nan, "up": np.nan, "lw": np.nan})
            distro.append({"snr": [], "p": [], "size": size})
            req_snr.append(np.nan)
            rel.append(0)

    return normal, distro, req_snr, rel


def get_difference_nomral(base: list, comparison: list):
    return [{
        "snr": b["snr"] - c["snr"],
        "up": b["up"] - c["up"],
        "lw": b["lw"] - c["lw"]
    } for b, c in zip(base, comparison)]


def plot_errors_bars(dnorm: list, distro: list, path: Path):
    dsnr, dup, dlw = zip(*[(d["snr"], d["up"], d["lw"]) for d in dnorm])
    size = [e["size"] for e in distro]
    fig, ax = plt.subplots(constrained_layout=True)  # figsize=(12, 4)

    bar_width = 0.6 / 3
    x = np.arange(len(HOURS))

    ax.bar(x - bar_width, dsnr, color="#0052CC", lw=1, label=r"$\Delta\mathrm{SNR}$", width=bar_width)
    ax.bar(x, dup, color="#CC0000", lw=1, label=r"$\Delta \sigma_\mathrm{UP}$", width=bar_width)
    ax.bar(x + bar_width, dlw, color="#2CA02C", lw=1, label=r"$\Delta \sigma_\mathrm{LW}$", width=bar_width)

    ax.set_title("Hourly VOACAP Parameter Deviations from WSPR")
    ax.set_ylabel("Deviation (dB)")
    ax.set_xlabel("Hour (UTC)")

    ax.set_xticks(x)
    ax.margins(x=0.01, y=0.01)

    ax.legend()
    ax.minorticks_on()
    ax.grid(True, which='major', alpha=0.5)
    ax.grid(True, which='minor', alpha=0.3)

    ax_top = ax.twiny()
    ax_top.set_xlim(ax.get_xlim())  # sync the range
    ax_top.set_xticks(x)
    ax_top.set_xticklabels(size, rotation=45, ha="left")
    ax_top.xaxis.set_ticks_position("top")
    ax_top.xaxis.set_label_position("top")
    ax_top.set_xlabel("Sample Size")

    avg_dsnr = np.nanmean(np.abs(np.array(dsnr)))
    avg_dup = np.nanmean(np.abs(np.array(dup)))
    avg_dlw = np.nanmean(np.abs(np.array(dlw)))
    latex_caption = (
        rf"Average deviations:"
        rf"\\$\overline{{\Delta \mathrm{{SNR}}}} = {avg_dsnr:.2f}\,\mathrm{{dB}}$"
        rf"\\$\overline{{\Delta \sigma_\mathrm{{UP}}}} = {avg_dup:.2f}\,\mathrm{{dB}}$"
        rf"\\$\overline{{\Delta \sigma_\mathrm{{LW}}}} = {avg_dlw:.2f}\,\mathrm{{dB}}$"
    )

    path = path / "error_bars.pdf"
    CAPTIONS[str(path)] = latex_caption

    fig.savefig(path)
    plt.close(fig)


def plot_req_snr(req_snr: list, path: Path):
    data = np.array(req_snr)
    data = data[~np.isnan(data)]

    mu, o = norm.fit(data)
    if o == 0: return
    o_off = 4
    x = np.linspace(mu - o_off * o, mu + o_off * o, 300)
    pdf = norm.pdf(x, mu, o)

    fig, ax = plt.subplots(constrained_layout=True)  # figsize=(10, 10),

    ax.plot(x, pdf, lw=1, color="#0052CC")
    ax.fill_between(x, 0, pdf, alpha=0.2)

    ax.set_title(f"WSPR Fitted Bottom 1% SNR Distribution (Offset)")
    ax.set_ylabel("Probability Density")
    ax.set_xlabel("SNR (dB)")

    ax.margins(x=0, y=0)
    ymin, ymax = ax.get_ylim()
    padding = 0.05 * (ymax - ymin)
    ax.set_ylim(ymin, ymax + padding)

    ax.minorticks_on()
    ax.grid(True, which='major', alpha=0.5)
    ax.grid(True, which='minor', alpha=0.3)

    latex_caption = (
        rf"\\REQ SNR estimation"
        rf"\\Sample size: $n = {len(data)}$"
        rf"\\Fitted Normal: $\mu = {mu:.2f}$ dB,\quad $\sigma = {o:.2f}$ dB"
    )

    path = path / f"low_req_snr.pdf"
    CAPTIONS[str(path)] = latex_caption

    fig.savefig(path)
    plt.close(fig)


def plot_hour_normal_distros(wspr_norm: list, voacap_norm: list, wspr_distro: list, path: Path):
    for H in HOURS:
        hour_distro = wspr_distro[H]
        if not hour_distro["snr"]: continue

        # Parameters for two split normal distributions
        wspr = wspr_norm[H]
        mu1 = wspr["snr"]
        o_l1 = wspr["lw"]
        o_u1 = wspr["up"]

        voacap = voacap_norm[H]
        mu2 = voacap["snr"]
        o_l2 = voacap["lw"]
        o_u2 = voacap["up"]

        if o_l1 == 0 or o_u1 == 0 or o_l2 == 0 or o_u2 == 0: continue

        A1, A2 = np.sqrt(2 / np.pi) / (o_l1 + o_u1), np.sqrt(2 / np.pi) / (o_l2 + o_u2)

        # Generate x values over a range covering both distributions
        o_off = 4
        x = np.linspace(
            min(hour_distro["snr"][0], mu1 - o_off * o_u1, mu2 - o_off * o_u2),
            max(hour_distro["snr"][-1], mu1 + o_off * o_u1, mu2 + o_off * o_u2),
            300
        )

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

        label1, = ax.plot(hour_distro["snr"], hour_distro["p"], lw=1, color="#0052CC", label="WSPR Observed")
        ax.fill_between(hour_distro["snr"], 0, hour_distro["p"], alpha=0.2)
        label2, = ax.plot(x, pdf1, lw=1, color="#CC0000", label="WSPR Fitted")
        ax.fill_between(x, 0, pdf1, alpha=0.2)
        label3, = ax.plot(x, pdf2, lw=1, color="#2CA02C", label="VOACAP Prediction")
        ax.fill_between(x, 0, pdf2, alpha=0.2)

        ax.set_title(f"SNR Distribution at Hour {H:02d} (UTC)")
        ax.set_ylabel("Probability Density")
        ax.set_xlabel("SNR (dB)")

        ax.margins(x=0, y=0)
        ymin, ymax = ax.get_ylim()
        padding = 0.05 * (ymax - ymin)
        ax.set_ylim(ymin, ymax + padding)

        ax.legend(handles=[label1, label2, label3], framealpha=0.5)
        ax.minorticks_on()
        ax.grid(True, which='major', alpha=0.5)
        ax.grid(True, which='minor', alpha=0.3)

        latex_caption = (
            rf"\\WSPR sample size: $n = {hour_distro["size"]}$"
            rf"\\WSPR: $\mu = {int(mu1) if not np.isnan(mu1) else "nan"}$,\quad $\sigma_{{\mathrm{{UP}}}} = {o_u1:.2f}$,\quad $\sigma_{{\mathrm{{LW}}}} = {o_l1:.2f}$"
            rf"\\VOACAP: $\mu = {int(mu2) if not np.isnan(mu2) else "nan"}$,\quad $\sigma_{{\mathrm{{UP}}}} = {o_u2:.2f}$,\quad $\sigma_{{\mathrm{{LW}}}} = {o_l2:.2f}$"
        )

        file_path = path / f"normal_h{H:02d}.pdf"
        CAPTIONS[str(file_path)] = latex_caption

        fig.savefig(file_path)
        plt.close(fig)


def make_point_plots(path: Path, band: str, snr: list[float], snr_up: list[float], snr_lw: list[float]):
    dir_path = FIGURE_POINT_PATH / path.relative_to(path.parent.parent) / band
    dir_path.mkdir(parents=True, exist_ok=True)

    voacap_norm = [{
        "snr": s - SNR_OFFSET,
        "up": np.nan if up == 0 else abs(up / 1.28),
        "lw": np.nan if lw == 0 else abs(lw / 1.28)
    } for s, up, lw in zip(snr, snr_up, snr_lw)]

    wspr_norm, wspr_distro, wspr_req_snr, wrel = get_per_hour_distros(path / f"{band}.json")
    print("WSPR REL:", [f"{v:.2f}" for v in wrel], sep="\t")

    irel: list[float] = []
    for n in wspr_norm:
        o = n["lw"] if REQ_SNR > n["snr"] else n["up"]
        irel.append(norm.cdf((n["snr"] - REQ_SNR) / o) if o != 0 else np.nan)
    print("INTR REL:", [f"{v:.2f}" if not np.isnan(v) else " nan" for v in irel], sep="\t")

    dnorm = get_difference_nomral(wspr_norm, voacap_norm)
    WSPR_NORM.setdefault(path.parent.name, {})[band] = wspr_norm

    plot_errors_bars(dnorm, wspr_distro, dir_path)
    plot_req_snr(wspr_req_snr, dir_path)
    plot_hour_normal_distros(wspr_norm, voacap_norm, wspr_distro, dir_path)


def plot_group_errors_bars(dicts: list, band, center, path: Path):
    rx, dist, dnorm, size = zip(*[(d["rx"], d["dist"], d["dnorm"], d["samples"]) for d in dicts])
    avg_dsnr, avg_dup, avg_dlw = [], [], []

    for dn in dnorm:
        snr, up, lw = zip(*[(d["snr"], d["up"], d["lw"]) for d in dn])

        avg_dsnr.append(np.nanmean(np.abs(np.array(snr))))
        avg_dup.append(np.nanmean(np.abs(np.array(up))))
        avg_dlw.append(np.nanmean(np.abs(np.array(lw))))

    fig, ax = plt.subplots(constrained_layout=True)

    count = 0
    for i, (label, x, snr, up, lw) in enumerate(zip(rx, dist, avg_dsnr, avg_dup, avg_dlw)):
        if snr == np.nan or up == np.nan or lw == np.nan: continue
        ax.errorbar(x, snr, yerr=[[lw], [up]], fmt='o', capsize=4, label=label.replace("∕", "/"))
        count += 1

    if count == 0:
        plt.close(fig)
        return

    ax.set_xlabel(rf"$\Delta\mathrm{{Distance}}$ from {center.replace("∕", "/")}")
    ax.set_ylabel(rf"$\overline{{|\Delta\mathrm{{SNR}}|}}$")
    ax.set_title(f"Average Deviations from {center.replace("∕", "/")} (Band: {band})")
    ax.margins(x=0.1, y=0.1)

    ax.minorticks_on()
    ax.grid(True, which='major', alpha=0.5)
    ax.grid(True, which='minor', alpha=0.3)

    ax.legend(ncol=1,
              fontsize='x-small',
              handlelength=0,
              handletextpad=0.5,
              borderaxespad=0,
              bbox_to_anchor=(1.01, 1),
              loc='upper left')

    latex_caption = "\\\\" + ", ".join(
        rf"{beacon}: sample size $= {n}$" for beacon, n in zip(rx, size)
    )

    file_path = path / f"error_{band}.pdf"
    CAPTIONS[str(file_path)] = latex_caption

    fig.savefig(file_path)
    plt.close(fig)


def make_group_plots(path: Path, band: str, beacon_dist):
    global WSPR_NORM

    WSPR_NORM = json.load(open("data/wspr_norm.json"))
    POWER = json.load(open("data/power.json"))

    if path.parent.name not in WSPR_NORM or band not in WSPR_NORM[path.parent.name]:
        return
    power = POWER[path.parent.name]
    wspr_norm = WSPR_NORM[path.parent.name][band]
    for entry in wspr_norm:
        entry["snr"] -= power

    RX = path.parent.name.split("_")[1]
    dir_path = FIGURE_GROUP_PATH / path.relative_to(path.parent.parent)
    dir_path.mkdir(parents=True, exist_ok=True)

    # Get hourly normal snr distro and total sample size per beacon
    jsons = sorted(path.glob(f"{band}/*.json"))
    group = {file_path.stem.split("_")[1]: {"norm": norm, "samples": samples}
             for file_path in jsons
             for norm, _, _, samples in [get_per_hour_distros(file_path)]
             }

    # Filer out when one of the beacons lacks data in a band
    dicts = []
    for rx in group:
        power = POWER[f"{path.parent.name.split("_")[0]}_{rx}"]
        group_norm = group[rx]["norm"]
        for entry in group_norm:
            entry["snr"] -= power

        dnorm = get_difference_nomral(wspr_norm, group_norm)

        if all(all(np.isnan(v) for v in d.values()) for d in dnorm):
            continue

        dicts.append({
            "rx": rx,
            "dist": beacon_dist[f"{RX}_{rx}"],
            "dnorm": dnorm,
            "samples": group[rx]["samples"]
        })

    if len(dicts) != 0:
        plot_group_errors_bars(dicts, band, RX, dir_path)
