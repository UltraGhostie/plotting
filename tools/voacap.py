import subprocess
from pathlib import Path


def run_voacap(MONTH, SSN, TX, RX, CIRCUIT, NOISE, POWER):
    config = f"""\
LINEMAX    9999       number of lines-per-page
COEFFS    CCIR
TIME          1   24    1    1
MONTH      {MONTH}
SUNSPOT    {SSN}
LABEL     {TX}              {RX}
CIRCUIT   {CIRCUIT}  S     0
SYSTEM       1. {NOISE}. 3.00  90. 3.0 3.00 0.10
FPROB      1.00 1.00 1.00 0.00
ANTENNA       1    1    2    5     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    2    5    6     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    3    6    8     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    4    8   12     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    5   12   15     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    6   15   19     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    7   19   22     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    8   22   26     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       1    9   26   30     0.000[default/isotrope     ]  0.0    {POWER}
ANTENNA       2   10    2    5     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   11    5    6     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   12    6    8     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   13    8   12     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   14   12   15     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   15   15   19     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   16   19   22     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   17   22   26     0.000[default/isotrope     ]  0.0    0.0000
ANTENNA       2   18   26   30     0.000[default/isotrope     ]  0.0    0.0000
FREQUENCY  3.60 5.30 7.1010.1014.1018.1021.1024.9028.20 0.00 0.00
METHOD       30    0
EXECUTE
QUIT"""
    config_path = Path.home() / "itshfbc/run/voacapx.dat"
    output_path = Path.home() / "itshfbc/run/voacapx.out"

    config_path.write_text(config)
    subprocess.run(["voacapl", str(Path.home() / "itshfbc")], check=True)

    path = Path("data") / "data" / f"{TX}_{RX}" / f"{MONTH.replace(" ", "_")}"
    path.mkdir(parents=True, exist_ok=True)
    output_path.rename(path / "voacapx.out")
