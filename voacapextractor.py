import argparse



parser = argparse.ArgumentParser("VOACAPextractor")
_ = parser.add_argument("hour", help="The hour that will extracted from")
_ = parser.add_argument("field", help="The field that will extracted")
_ = parser.add_argument("-i", "--input", 
                        help="The file to extract data from. Default ~/itshfbc/run/voacapx.out",
                        required=False,
                        default="/home/theodorb/itshfbc/run/voacapx.out")
_ = parser.add_argument("-f", "--frequency", 
                        help="The frequency that will extracted. Default all",
                        required=False,
                        default="all",
                        choices=['10', '14', '7', '21', '24', '28', 'all'])

args = parser.parse_args()


hour = int(args.hour)
field = args.field


dataFile = open(args.input)

line = ""
h = -1


while not h == hour:
    line = dataFile.readline()
    while not line.endswith("FREQ\n") :
        line = dataFile.readline()

    line = line.lstrip()
    h = int(line.split(".")[0])
    

while not line.endswith(field.upper()) :
    line = dataFile.readline().strip()


prevalues = line.split(" ")
values = list()

for value in prevalues:
    if value.strip().__len__() > 0 and not value ==  "-" and not value == field: 
        values.append(value)


if args.frequency == '11':
    print(values[0])

if args.frequency == '10':
    print(values[1])
if args.frequency == '14':
    print(values[2])
if args.frequency == '7':
    print(values[3])
if args.frequency == '21':
    print(values[4])
if args.frequency == '24':
    print(values[5])
if args.frequency == '28':
    print(values[6])
if args.frequency == 'all':
    for value in values:
        print(value)
