import argparse
from pathlib import Path

frequencies = ['3', '5', '7', '10', '14', '18', '21', '24', '28', 'all']

parser = argparse.ArgumentParser("VOACAPextractor")
_ = parser.add_argument("hour", help="The hour that will extracted from")
_ = parser.add_argument("field", help="The field that will extracted")
_ = parser.add_argument("-i", "--input",
                        help="The file to extract data from. Default ~/itshfbc/run/voacapx.out",
                        required=False,
                        default=Path.home() / "itshfbc/run/voacapx.out")
_ = parser.add_argument("-f", "--frequency",
                        help="The frequency that will extracted. Default all",
                        required=False,
                        default="all",
                        choices=frequencies)

args = parser.parse_args()

hour = int(args.hour)
field = args.field
dataFile = open(args.input)

line = ""
h = -1

while not h == hour:
    line = dataFile.readline()
    while not line.endswith("FREQ\n"):
        line = dataFile.readline()

    line = line.lstrip()
    h = int(line.split(".")[0])

while not line.endswith(field.upper()):
    line = dataFile.readline().strip()

prevalues = line.split(" ")
values = list()
for value in prevalues:
    if value.strip().__len__() > 0 and not value == "-" and not value == field:
        values.append(value)
values.pop(0)  # Skip MRM frequency values

if args.frequency != 'all':
    index = frequencies.index(args.frequency)
    print(values[index])
else:
    for value in values:
        print(value)
