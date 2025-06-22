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

DATA_TABLE_PATH: Path = Path("data/data/table")

FIGURE_POINT_PATH: Path = Path("data/figures/point")
FIGURE_GROUP_PATH: Path = Path("data/figures/group")
FIGURE_TABLE_PATH: Path = Path("data/figures/table")

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
            rel.append(np.nan)

    return normal, distro, req_snr, rel, len(data)


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


def plot_req_snr(req_snr: list, band:str, table_path:Path, path: Path):
    data = np.array(req_snr)
    data = data[~np.isnan(data)]

    mu, o = norm.fit(data)
    if o == 0: return

    file_path = table_path / "DATA.json"
    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
            data[band] = REL
    else:
        data = {band: REL}
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

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


def calculate_point_rel(wspr_norm: list[dict[str, float]], voacap_rel: list[float], count_rel: list[float], band: str,
                        path: Path):
    REL = {}
    interp_rel: list[float] = []
    for n in wspr_norm:
        o = n["lw"] if REQ_SNR > n["snr"] else n["up"]
        interp_rel.append(norm.cdf((n["snr"] - REQ_SNR) / o) if o != 0 else np.nan)
    # interp_rel = list(np.nan_to_num(interp_rel, nan=0.0))
    diff_rel = list(np.abs(np.subtract(interp_rel, voacap_rel)))

    REL["WSPR"] = {"avg": np.nanmean(interp_rel), "rel": interp_rel}
    # REL["DATA"] = {"avg":np.nanmean(count_rel), "rel":count_rel}
    REL["VOACAP"] = {"avg": np.nanmean(voacap_rel), "rel": voacap_rel}
    REL["DIFF"] = {"avg": np.nanmean(diff_rel), "rel": diff_rel}

    file_path = path / "DATA.json"
    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
            data["REL"][band] = REL
    else:
        data = {"REL": {band: REL}}
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    print("Reliabilty")
    print(
        "WSPR",
        f"{np.nanmean(interp_rel):.2f}",
        [f"{v:.2f}" if not np.isnan(v) else " -- " for v in interp_rel],
        sep="\t"
    )
    """print(
        "DATA",
        f"{np.nanmean(count_rel):.2f}",
        [f"{v:.2f}" if not np.isnan(v) else " -- " for v in count_rel],
        sep="\t"
    )"""
    print(
        "VOA ",
        f"{np.nanmean(voacap_rel):.2f}",
        [f"{v:.2f}" if not np.isnan(v) else " -- " for v in voacap_rel],
        sep="\t"
    )
    print(
        "DIFF",
        f"{np.nanmean(diff_rel):.2f}",
        [f"{v:.2f}" if not np.isnan(v) else " -- " for v in diff_rel],
        sep="\t"
    )
    print()


def calculate_point_score(wspr_norm: list[dict[str, float]], voacap_norm: list[dict[str, float]], path: Path):
    cohen = []
    lvr_up = []
    lvr_lw = []
    for w, v in zip(wspr_norm, voacap_norm):
        ws, wu, wl = w["snr"], w["up"], w["lw"]
        vs, vu, vl = v["snr"], v["up"], v["lw"]

        cohen.append(np.divide(vs - ws, np.sqrt((wu ** 2 + wl ** 2 + vu ** 2 + vl ** 2) / 4)))

        if wu != 0 and vu != 0:
            lvr_up.append(np.log(vu / wu))
        else:
            lvr_up.append(np.nan)

        if wl != 0 and vl != 0:
            lvr_lw.append(np.log(vl/ wl))
        else:
            lvr_lw.append(np.nan)
    vs_u, vs_o = 2.0, 0.4
    s_u, s_o = 4.00, 0.8
    m_u, m_o = 6.00, 1.2
    l_u, l_o = 8.00, 1.6
    vl_u, vl_o = 10.0, 2.0
    h_u, h_o = 14.0, 2.2
    print("\t\t\t  Cohen\tLVR(UP)\t LVR(LW)")
    print(
        "Very small:",
        sum(abs(v) <= vs_u for v in cohen),
        sum(abs(v) <= vs_o for v in lvr_up),
        sum(abs(v) <= vs_o for v in lvr_lw),
        sep="\t\t")
    print(
        "Small:\t",
        sum(vs_u < abs(v) <= s_u for v in cohen),
        sum(vs_o < abs(v) <= s_o for v in lvr_up),
        sum(vs_o < abs(v) <= s_o for v in lvr_lw),
        sep="\t\t")
    print(
        "Medium:\t",
        sum(s_u < abs(v) <= m_u for v in cohen),
        sum(s_o < abs(v) <= m_o for v in lvr_up),
        sum(s_o < abs(v) <= m_o for v in lvr_lw),
        sep="\t\t")
    print(
        "Large:\t",
        sum(m_u < abs(v) <= l_u for v in cohen),
        sum(m_o < abs(v) <= l_o for v in lvr_up),
        sum(m_o < abs(v) <= l_o for v in lvr_lw),
        sep="\t\t")
    print(
        "Very Large:",
        sum(l_u < abs(v) <= vl_u for v in cohen),
        sum(l_o < abs(v) <= vl_o for v in lvr_up),
        sum(l_o < abs(v) <= vl_o for v in lvr_lw),
        sep="\t\t")
    print(
        "Huge:\t",
        sum(vl_u < abs(v) <= h_u for v in cohen),
        sum(vl_o < abs(v) <= h_o for v in lvr_up),
        sum(vl_o < abs(v) <= h_o for v in lvr_lw),
        sep="\t\t")
    print(
        "Crazy:\t",
        sum(h_u < abs(v) for v in cohen),
        sum(h_o < abs(v) for v in lvr_up),
        sum(h_o < abs(v) for v in lvr_lw),
        sep="\t\t")

    file_path = path / "DATA.json"
    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
            data["Score"]["cohen's d"].extend(cohen)
            data["Score"]["lvr_up"].extend(lvr_up)
            data["Score"]["lvr_lw"].extend(lvr_lw)

            data["Score"]["cohen's d"] = np.sort(data["Score"]["cohen's d"]).tolist()
            data["Score"]["lvr_up"] = np.sort(data["Score"]["lvr_up"]).tolist()
            data["Score"]["lvr_lw"] = np.sort(data["Score"]["lvr_lw"]).tolist()
    else:
        data = {"Score":
            {
            "cohen's d": np.sort(cohen).tolist(),
            "lvr_up": np.sort(lvr_up).tolist(),
            "lvr_lw": np.sort(lvr_lw).tolist()
            }
        }
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    #"""
    print()
    print(
        "COHEN:",
        f"{np.nanmean(np.abs(cohen)):.2f}",
        [f"{v:.2f}" if not np.isnan(v) else " -- " for v in cohen],
        sep="\t"
    )
    print(
        "LVR_U:",
        f"{np.nanmean(np.abs(lvr_up)):.2f}",
        [f"{v:.2f}" if not np.isnan(v) else " -- " for v in lvr_up],
        sep="\t"
    )
    print(
        "LVR_L",
        f"{np.nanmean(np.abs(lvr_lw)):.2f}",
        [f"{v:.2f}" if not np.isnan(v) else " -- " for v in lvr_lw],
        sep="\t"
    )
    #"""
    print()


"""def magic():
    path = Path("data/data/table/TI4JWC_KPH/2025_01.00")
    with open(path / "Scores.json", "r") as f:
        data = json.load(f)
        if not data: return
        cohen = np.sort(np.abs(data["cohen's d"]))
        up = np.sort(np.abs(data["lvr_up"]))
        lw = np.sort(np.abs(data["lvr_lw"]))

        val1, count1 = zip(*Counter(np.round(cohen[~np.isnan(cohen)], 0)).items())
        val2, count2 = zip(*Counter(np.round(up[~np.isnan(up)], 1)).items())
        val3, count3 = zip(*Counter(np.round(lw[~np.isnan(lw)], 1)).items())

        fig, ax = plt.subplots(constrained_layout=True)  # figsize=(10, 10),

        # ax.plot(val1[:23], np.divide(count1[:23], len(count1[:23])), lw=1, color="#0052CC", label="Cohen's d")
        # ax.fill_between(cohen, alpha=0.2)
        ax.plot(val2, np.divide(count2[:], len(count2[:])), lw=1, color="#CC0000", label="LVR$_{UP}$")
        # ax.fill_between(x, 0, pdf1, alpha=0.2)
        ax.plot(val3, np.divide(count3[:], len(count3[:])), lw=1, color="#2CA02C", label="LVR$_{LW}$")
        # ax.fill_between(x, 0, pdf2, alpha=0.2)

        ax.set_ylabel("P")
        ax.set_xlabel("Score")

        ax.margins(x=0, y=0)
        ymin, ymax = ax.get_ylim()
        padding = 0.05 * (ymax - ymin)
        ax.set_ylim(ymin, ymax + padding)

        ax.legend(framealpha=0.5)
        ax.minorticks_on()
        ax.grid(True, which='major', alpha=0.5)
        ax.grid(True, which='minor', alpha=0.3)

        fig.savefig(path / "Scores.pdf")
        plt.close(fig)"""


def make_point_plots(path: Path, band: str, snr: list[float], snr_up: list[float], snr_lw: list[float],
                     voacap_rel: list[float]):
    point_path = FIGURE_POINT_PATH / path.relative_to(path.parent.parent) / band
    table_path = DATA_TABLE_PATH / path.relative_to(path.parent.parent)
    point_path.mkdir(parents=True, exist_ok=True)
    table_path.mkdir(parents=True, exist_ok=True)

    voacap_norm = [{
        "snr": s - SNR_OFFSET,
        "up": np.nan if up == 0 else abs(up / 1.28),
        "lw": np.nan if lw == 0 else abs(lw / 1.28)
    } for s, up, lw in zip(snr, snr_up, snr_lw)]

    wspr_norm, wspr_distro, wspr_req_snr, count_rel, _ = get_per_hour_distros(path / f"{band}.json")

    WSPR_NORM.setdefault(path.parent.name, {})[band] = wspr_norm

    calculate_point_score(wspr_norm, voacap_norm, table_path)
    calculate_point_rel(wspr_norm, voacap_rel, count_rel, band, table_path)
    plot_errors_bars(get_difference_nomral(voacap_norm, wspr_norm), wspr_distro, point_path)
    plot_req_snr(wspr_req_snr, band, table_path, point_path)
    plot_hour_normal_distros(wspr_norm, voacap_norm, wspr_distro, point_path)


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
             for norm, _, _, _, samples in [get_per_hour_distros(file_path)]
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
