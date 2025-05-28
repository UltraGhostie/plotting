from pathlib import Path


def get_band(filepath: Path):
    with open(filepath) as file:
        for line in file:
            line = line.strip()
            if line.endswith("FREQ"):
                break

        parts = line.split()
        return [int(float(x)) for x in parts[2:-1] if int(float(x)) != 0]


def get_values(field: str, filepath: Path):
    data = []

    with open(filepath) as file:
        while True:
            for line in file:
                line = line.strip()
                if line.endswith("FREQ"):
                    break
            else:
                break  # EOF
            parts = line.split()

            hour = int(float(parts[0]))
            freqs = [int(float(x)) for x in parts[2:-1] if int(float(x)) != 0]

            for line in file:
                line = line.strip()
                if line.endswith(field):
                    break
            else:
                break  # EOF

            line = line[:-len(field)].strip()
            parts = line.split()

            values = [float(x) for x in parts[1:] if x != '-']
            for f, v in zip(freqs, values):
                data.append({"hour": hour, "freq": f, "value": v})

    return data


def extract(field: str, filepath: Path, hour: int = None, band: int = None):
    data = get_values(field, filepath)
    if hour is not None:
        data = [e for e in data if e["hour"] == hour]
    if band is not None:
        data = [e for e in data if e["freq"] == band]
    return data
