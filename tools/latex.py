import json
from datetime import datetime
from pathlib import Path
from itertools import zip_longest
from unicodedata import category

import numpy as np

DATA_TEMP_PATH: Path = Path("data/data/temp")

FIGURE_TABLE_PATH: Path = Path("data/figures/table")
FIGURE_POINT_PATH: Path = Path("data/figures/point")
FIGURE_GROUP_PATH: Path = Path("data/figures/group")

CAPTIONS = {}
fig_count = 1


def write_section(tx: str, rx: str, f):
    f.write(f"\\section*{{\\textbf{{TX}}:{tx} \\quad | \\quad \\textbf{{RX}}:{rx}}}\n".replace("∕", "/"))


def write_subsection(month: str, f):
    f.write(f"\t\\subsection*{{\\large\\textbf{{{month}}}}}\n")


def write_subsubsection(band: str, f):
    f.write(f"\t\t\\subsubsection*{{\\normalsize\\textbf{{Band: {band}}}}}\\hspace{{0pt}}\n")


def write_figure_block(path: Path, f):
    f.write(
        "                \\centering\n"
        "                \\begin{minipage}{0.497\\textwidth}\n"
        "                    \\centering\n"
        f"                    \\includegraphics[width=\\textwidth]{{{path}}}\n"
        f"                        \\caption{{{CAPTIONS.get(str(path), "Caption Lost").replace("∕", "/")}}}\n"
        f"                        \\label{{fig:{str(path).replace("data/figure/", "").replace("∕", "/").replace('/', '-')}}}\n"
        "                \\end{minipage}\n"
    )


def gen_point_figures():
    global fig_count
    output_path = Path("data/import_point_figures.tex")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        beacon_dirs = sorted([p for p in FIGURE_POINT_PATH.glob("*") if p.is_dir()])

        for beacon_path in beacon_dirs:
            tx, rx = beacon_path.name.split("_")
            write_section(tx, rx, f)
            month_dirs = sorted([p for p in beacon_path.glob("*") if p.is_dir()])

            for month_path in month_dirs:
                month = datetime.strptime(month_path.name, "%Y_%m.00").strftime("%B %Y")
                write_subsection(month, f)
                band_dirs = sorted([p for p in month_path.glob("*") if p.is_dir()])

                for band_path in band_dirs:
                    write_subsubsection(band_path.name, f)
                    fig_dirs = sorted(band_path.glob("*.pdf"))

                    # fig_count+=1    #compensate for sections
                    for left, right in zip_longest(fig_dirs[::2], fig_dirs[1::2]):
                        f.write("\t\t\t\\begin{figure}[!ht]\n")
                        write_figure_block(left, f)
                        if right:
                            f.write("\t\t\t\t\\hfill\n")
                            write_figure_block(right, f)
                        f.write("\t\t\t\\end{figure}\n")
                        if fig_count % 2 == 0: f.write("\\clearpage\n")
                        fig_count += 1


def gen_group_figures():
    global fig_count
    output_path = Path("data/import_group_figures.tex")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        beacon_dirs = sorted([p for p in FIGURE_GROUP_PATH.glob("*") if p.is_dir()])

        for beacon_path in beacon_dirs:
            tx, rx = beacon_path.name.split("_")
            write_section(tx, rx, f)
            month_dirs = sorted([p for p in beacon_path.glob("*") if p.is_dir()])

            for month_path in month_dirs:
                month = datetime.strptime(month_path.name, "%Y_%m.00").strftime("%B %Y")
                write_subsection(month, f)

                fig_dirs = sorted(month_path.glob("*.pdf"))
                for left, right in zip_longest(fig_dirs[::2], fig_dirs[1::2]):
                    f.write("\t\t\t\\begin{figure}[!ht]\n")
                    write_figure_block(left, f)
                    if right:
                        f.write("\t\t\t\t\\hfill\n")
                        write_figure_block(right, f)
                    f.write("\t\t\t\\end{figure}\n")
                    if fig_count % 2 == 0: f.write("\\clearpage\n")
                    fig_count += 1


def gen_req_snr(REQ_SNR, path: Path):
    file_path = path / "REQ_SNR.tex"
    lines = []
    lines.append(r"\begin{table}[!ht]")
    lines.append(r"\centering")
    lines.append(r"\begin{tabular}{|c|c|} \hline")
    lines.append(rf"\multicolumn{{2}}{{|c|}}{{\textbf{{{path.parent.name.replace("_", " -- ")}}}}} \\ \hline")
    lines.append(r"\textbf{Band} & \textbf{SNR [dB]} \\ \hline")

    mus = np.array([])
    sds = np.array([])
    ns = np.array([])
    for band, req_snr in REQ_SNR.items():
        mu = req_snr["mu"]
        sd = req_snr["o"]
        n = req_snr["n"]

        mus = np.append(mus, mu)
        sds = np.append(sds, sd)
        ns = np.append(ns, n)

        lines.append(f"\t\\textbf{{{band:2}}} & ${mu:.2f} \\pm {sd:.2f}$ \\\\ \\hline")

    pooled_sd = np.sqrt(np.sum((ns - 1) * sds ** 2) / np.sum(ns - 1))
    lines.append(r"\textbf{Average} & " + rf"{{\boldmath ${np.mean(mus):.2f} \pm {pooled_sd:.2f}$}} \\ \hline")
    lines.append(r"\end{tabular}")
    lines.append(rf"\caption{{Bottom 1\% SNR}}")
    lines.append(rf"\label{{tab:{str(file_path)}}}")
    lines.append(r"\end{table}")

    open(file_path, "w").write("\n".join(lines))


def gen_rel(REL, path: Path):
    for band, val in REL.items():
        file_path = path / f"REL_{band}.tex"

        avg_w, rel_w = val["WSPR"]["avg"], val["WSPR"]["rel"]
        avg_v, rel_v = val["VOACAP"]["avg"], val["VOACAP"]["rel"]
        avg_d, rel_d = val["DIFF"]["avg"], val["DIFF"]["rel"]

        lines = []
        lines.append(r"\begin{table}[!ht]")
        lines.append(r"\centering")
        lines.append(r"\begin{tabular}{|c|c|c|c|} \hline")
        lines.append(rf"\multicolumn{{4}}{{|c|}}{{\textbf{{{path.parent.name.replace("_", " -- ")}}}}} \\ \hline")
        lines.append(r"\textbf{Hour} & \textbf{WSPR} & \textbf{VOACAP} & \textbf{$\Delta$REL} \\ \hline")

        for h, (w, v, d) in enumerate(zip(rel_w, rel_v, rel_d)):
            w = "-" if np.isnan(w) else f"{w:.2f}"
            v = "-" if np.isnan(v) else f"{v:.2f}"
            d = "-" if np.isnan(d) else f"{d:.2f}"
            lines.append(f"\t\\textbf{{{h:2}}}\t& ${w:^4}$\t& ${v:^4}$\t& ${d:^4}$ \\\\ \\hline")

        lines.append(
            rf"\textbf{{Average}} & {{\boldmath ${avg_w:.2f}$}} & {{\boldmath ${avg_v:.2f}$}} & {{\boldmath ${avg_d:.2f}$}} \\ \hline")
        lines.append(r"\end{tabular}")
        lines.append(rf"\caption{{Reliability Comparison (Band: {band})}}")
        lines.append(rf"\label{{tab:{str(file_path)}}}")
        lines.append(r"\end{table}")

        open(file_path, "w").write("\n".join(lines))
    # ------------------------------------------------
    file_path = path / "SMOL_REL.tex"

    lines = []
    lines.append(r"\begin{table}[!ht]")
    lines.append(r"\centering")
    lines.append(r"\begin{tabular}{|c|c|c|c|} \hline")
    lines.append(rf"\multicolumn{{4}}{{|c|}}{{\textbf{{{path.parent.name.replace("_", " -- ")}}}}} \\ \hline")
    lines.append(
        r"\textbf{Band} \rule{0pt}{2.5ex} & $\overline{\mathrm{\textbf{WSPR}}}$ & $\overline{\mathrm{\textbf{VOACAP}}}$ & $\overline{\Delta\mathrm{\textbf{REL}}}$ \\ \hline")

    AVG_W = []
    AVG_V = []
    AVG_D = []
    for band, val in REL.items():
        avg_w = val["WSPR"]["avg"]
        avg_v = val["VOACAP"]["avg"]
        avg_d = val["DIFF"]["avg"]
        AVG_W.append(avg_w)
        AVG_V.append(avg_v)
        AVG_D.append(avg_d)

        lines.append(f"\t\\textbf{{{band:2}}}\t& ${avg_w:.2f}$\t& ${avg_v:.2f}$\t& ${avg_d:.2f}$ \\\\ \\hline")
    lines.append(
        rf"\textbf{{Total}} & {{\boldmath ${np.mean(AVG_W):.2f}$}} & {{\boldmath ${np.mean(AVG_V):.2f}$}} & {{\boldmath ${np.mean(AVG_D):.2f}$}} \\ \hline")
    lines.append(r"\end{tabular}")
    lines.append(rf"\caption{{Reliability Comparison (Summary)}}")
    lines.append(rf"\label{{tab:{str(file_path)}}}")
    lines.append(r"\end{table}")

    open(file_path, "w").write("\n".join(lines))


def score(cohen, lvr_up, lvr_lw):
    cohen = np.asarray(cohen)
    lvr_up = np.asarray(lvr_up)
    lvr_lw = np.asarray(lvr_lw)

    vs_u, vs_o = 2.0, 0.4
    s_u, s_o = 4.00, 0.8
    m_u, m_o = 6.00, 1.2
    l_u, l_o = 8.00, 1.6
    vl_u, vl_o = 10.0, 2.0
    h_u, h_o = 14.0, 2.2

    categories = [
        ("Very Small", (float("-inf"), vs_u), (float("-inf"), vs_o)),
        ("Small", (vs_u, s_u), (vs_o, s_o)),
        ("Medium", (s_u, m_u), (s_o, m_o)),
        ("Large", (m_u, l_u), (m_o, l_o)),
        ("Very Large", (l_u, vl_u), (l_o, vl_o)),
        ("Huge", (vl_u, h_u), (vl_o, h_o)),
        ("Crazy", (h_u, float("inf")), (h_o, float("inf"))),
    ]

    result = {}
    for label, (u_l, u_h), (o_l, o_h) in categories:
        result[label] = (
            np.nansum((u_l < cohen) & (cohen <= u_h)),
            np.nansum((o_l < lvr_up) & (lvr_up <= o_h)),
            np.nansum((o_l < lvr_lw) & (lvr_lw <= o_h))
        )
    return result


def gen_score(SCORE, path: Path):
    COHEN = np.asarray([])
    UP = np.asarray([])
    LW = np.asarray([])
    for band, val in SCORE.items():
        file_path = path / f"SCORE_{band}.tex"

        cohen = np.asarray(val["cohen's d"])
        up = np.asarray(val["lvr_up"])
        lw = np.asarray(val["lvr_lw"])

        COHEN = np.append(COHEN, cohen)
        UP = np.append(UP, up)
        LW = np.append(LW, up)

        pos = score(cohen[cohen >= 0], up[up >= 0], lw[lw >= 0])
        neg = score(np.abs(cohen[cohen < 0]), np.abs(up[up < 0]), np.abs(lw[lw < 0]))

        lines = []
        lines.append(r"\begin{table}[!ht]")
        lines.append(r"\centering")
        lines.append(r"\begin{tabular}{|c|c|c|c|} \hline")
        lines.append(rf"\multicolumn{{4}}{{|c|}}{{\textbf{{{path.parent.name.replace("_", " -- ")}}}}} \\ \hline")
        lines.append(
            r"\textbf{Difference} & \boldmath$\Delta$\textbf{SNR} (+/-)& " +
            r"\boldmath{$\Delta\sigma_\mathrm{\textbf{UP}}$} (+/-) &  " +
            r"\boldmath{$\Delta\sigma_\mathrm{\textbf{LW}}$} (+/-)" +
            r" \\ \hline")
        for (label, (c_p, u_p, l_p)), (_, (c_n, u_n, l_n)) in zip(pos.items(), neg.items()):
            lines.append(
                rf"\textbf{{{label}}} & " +
                rf"{c_p}/{c_n} & " +
                rf"{u_p}/{u_n} & " +
                rf"{l_p}/{l_n}" +
                r" \\ \hline")

        lines.append(r"\end{tabular}")
        lines.append(rf"\caption{{Score Comparison (Band: {band})}}")
        lines.append(rf"\label{{tab:{str(file_path)}}}")
        lines.append(r"\end{table}")

        open(file_path, "w").write("\n".join(lines))
    # ------------------------------------------------
    file_path = path / "SMOL_SCORE.tex"

    POS = score(COHEN[COHEN >= 0], UP[UP >= 0], LW[LW >= 0])
    NEG = score(np.abs(COHEN[COHEN < 0]), np.abs(UP[UP < 0]), np.abs(LW[LW < 0]))

    lines = []
    lines.append(r"\begin{table}[!ht]")
    lines.append(r"\centering")
    lines.append(r"\begin{tabular}{|c|c|c|c|} \hline")
    lines.append(rf"\multicolumn{{4}}{{|c|}}{{\textbf{{{path.parent.name.replace("_", " -- ")}}}}} \\ \hline")
    lines.append(
        r"\textbf{Difference} & \boldmath$\Delta$\textbf{SNR} (+/-)& " +
        r"\boldmath{$\Delta\sigma_\mathrm{\textbf{UP}}$} (+/-) &  " +
        r"\boldmath{$\Delta\sigma_\mathrm{\textbf{LW}}$} (+/-)" +
        r" \\ \hline")
    for (label, (c_p, u_p, l_p)), (_, (c_n, u_n, l_n)) in zip(POS.items(), NEG.items()):
        lines.append(
            rf"\textbf{{{label}}} & " +
            rf"{c_p}/{c_n} & " +
            rf"{u_p}/{u_n} & " +
            rf"{l_p}/{l_n}" +
            r" \\ \hline")

    lines.append(r"\end{tabular}")
    lines.append(rf"\caption{{Score Comparison (Summary)}}")
    lines.append(rf"\label{{tab:{str(file_path)}}}")
    lines.append(r"\end{table}")

    open(file_path, "w").write("\n".join(lines))


def gen_tables():
    beacon_dirs = sorted([p for p in DATA_TEMP_PATH.glob("*") if p.is_dir()])
    for beacon_path in beacon_dirs:
        month_dirs = sorted([p for p in beacon_path.glob("*") if p.is_dir()])
        for month_path in month_dirs:
            table_path = FIGURE_TABLE_PATH / month_path.relative_to(month_path.parent.parent)
            table_path.mkdir(parents=True, exist_ok=True)
            data = json.load(open(month_path / "TEMP.json"))
            gen_req_snr(data["REQ SNR"], table_path)
            gen_rel(data["REL"], table_path)
            gen_score(data["SCORE"], table_path)


def gen_latex():
    global CAPTIONS
    CAPTIONS = json.load(open(Path("data/captions.json")))
    gen_point_figures()
    gen_group_figures()
    gen_tables()
