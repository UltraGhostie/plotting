import json
from datetime import datetime
from pathlib import Path
from itertools import zip_longest

FIGURE_POINT_PATH: Path = Path("data/figures/point")
CAPTIONS = {}

def write_section(tx: str, rx: str, f):
    f.write(f"\\section*{{\\textbf{{TX}}:{tx} \\quad | \\quad \\textbf{{RX}}:{rx}}}\n")


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
        f"                        \\caption{{{CAPTIONS.get(path, "Caption Lost")}}}\n"
        f"                        \\label{{fig:{str(path).replace("data/figure/", "").replace('/', '-')}}}\n"
        "                \\end{minipage}\n"
    )


def make_latex():
    global CAPTIONS
    output_path = Path("data/import_figures.tex")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    CAPTIONS = json.load(open(Path("data/captions.json")))

    fig_count = 1
    with open(output_path, "w") as f:
        beacon_dirs = sorted([p for p in FIGURE_POINT_PATH.glob("*") if p.is_dir()])

        for beacon_path in beacon_dirs:
            tx, rx = beacon_path.name.split("_")
            write_section(tx, rx, f)
            month_dirs = sorted([p for p in beacon_path.glob("*") if p.is_dir()])

            for month_path in month_dirs:
                month = datetime.strptime(month_path.name, "%Y_%m.00").strftime("%B %Y")
                write_subsection(month, f)
                band_dirs = sorted(
                    (p for p in month_path.glob("*") if p.name.isdigit()),
                    key=lambda p: int(p.name)
                )

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
                        if fig_count % 2 == 0: f.write("\\clearpage")
                        fig_count += 1
    CAPTIONS.clear()
