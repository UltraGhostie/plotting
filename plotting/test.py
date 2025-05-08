import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import psycopg2
import scipy.stats as stats
import statistics
import math
import argparse



parser = argparse.ArgumentParser("WSPRcomp")
_ = parser.add_argument("band", help="The band that will be fetched")
_ = parser.add_argument("predsnrs", help="Expected SNR values")
_ = parser.add_argument("predsnrups", help="Expected SNRup values")
_ = parser.add_argument("predsnrlws", help="Expected SNRlw values")
_ = parser.add_argument("sender", help="The sender in the circuit")
_ = parser.add_argument("receiver", help="The receiver in the circuit")
args = parser.parse_args()





band = args.band
mus = list()
for mu in args.predsnrs.split(" "):
    mus.append(float(mu)-34)

snrups = list()
for up in args.predsnrups.split(" "):
    up = float(up) / 1.28
    if up > 0:
        snrups.append(up)
    else:
        snrups.append(-up)

snrlws = list()
for lw in args.predsnrlws.split(" "):
    lw = float(lw)/1.28 
    if lw > 0: 
        snrlws.append(lw)
    else:
        snrlws.append(-lw)






host = "172.17.0.2"
user = "postgres"
db = "postgres"

conn = psycopg2.connect(dbname=db, user=user, host=host)
c = conn.cursor()



mu: list[float] = list()
sigmalw: list[float] = list()
sigmaup: list[float] = list()
nodata: list[int] = list()
for H in range(1, 24):
    query = "SELECT snr FROM wspr.rx WHERE " + "rx_sign = '" + args.receiver + "' AND tx_sign = '" + args.sender + "' AND band = " + band + " AND EXTRACT(HOUR FROM time) < " + str(H) + " AND EXTRACT(HOUR FROM time) >= " + str(H-1) + ";"
    c.execute(query)

    snrfull: list[int] = list()
    for res in c:
        snrfull.append(res[0])

    if len(snrfull) == 0: 
        snrfull.append(0)
        nodata.append(H)

    lw: list[float] = list()
    up: list[float] = list()

    median = statistics.median(snrfull)
    mu.append(median)
    for i in range(snrfull.__len__()):
        if i < (snrfull.__len__() - 1)/ 2:
            lw.append(snrfull[i]-median)
        else:
            up.append(snrfull[i]-median)

    sigmalw.append(0)
    if len(lw) > 1:
        for i in lw:
            sigmalw[H-1] += pow(i, 2)
        sigmalw[H-1] /= lw.__len__() - 1

    sigmaup.append(0)
    if len(up) > 1:
        for i in up:
            sigmaup[H-1] += pow(i, 2)
        sigmaup[H-1] /= up.__len__() - 1

    lw.append(0)


c.close()

conn.close()






hours = range(1, 24)
diff = list()
difflw = list()
diffup = list()
labels = list()
colors = list()

for i in hours:
    # print(str(mu[i-1]) + " " + str(mus[i-1]))
    diff.append(mu[i-1]-mus[i-1])
    difflw.append(snrlws[i-1]-sigmaup[i-1])
    diffup.append(snrups[i-1]-sigmaup[i-1])
    labels.append(str(i))
    colors.append("tab:blue")

for i in nodata:
    # diff[i-1] = 0
    # difflw[i-1] = 0
    # diffup[i-1] = 0
    colors[i-1] = ("tab:red")

# print(str(len(hours)))
# print(str(len(diff)))
# print(str(len(difflw)))
# print(str(len(diffup)))
# print(str(diffup[0]))
fix, (ax, axup, axlw, stack) = plt.subplots(1, 4)
# fix, ax = plt.subplots(1, 1)
# fix, axup = plt.subplots(1, 1)
# fix, axlw = plt.subplots(1, 1)
# fix, stack = plt.subplots(1, 1)
ax.bar(hours, diff, label=labels, color=colors)
ax.set_title("SNR Error in band " + str(band))
ax.set_ylabel("Error")
ax.set_xlabel("Hour")


axlw.bar(hours, difflw, label=labels, color=colors)
axlw.set_title("Sigmalw Error in band " + str(band))
axlw.set_ylabel("Error")
axlw.set_xlabel("Hour")

axup.bar(hours, diffup, label=labels, color=colors)
axup.set_title("Sigmaup Error in band " + str(band))
axup.set_ylabel("Error")
axup.set_xlabel("Hour")




conn = psycopg2.connect(dbname=db, user=user, host=host)
c = conn.cursor()

# GET SNR DIST
query = "SELECT COUNT(snr), snr FROM wspr.rx WHERE " + "band = " + band + " GROUP BY snr ORDER BY snr DESC;"
c.execute(query)
snr: list[int] = list()
count: list[int] = list()


for res in c:
    snr.append(res[1])
    count.append(res[0])





query = "SELECT snr FROM wspr.rx WHERE " + "band = " + band  + " ORDER BY snr DESC;"
c.execute(query)
snrfull: list[int] = list()
for res in c:
    snrfull.append(res[0])

c.close()
conn.close()





mu = statistics.median(snrfull)
lw: list[float] = list()
up: list[float] = list()

for i in range(snrfull.__len__()):
    if i < (snrfull.__len__() - 1)/ 2:
        lw.append(snrfull[i]-mu)
    else:
        up.append(snrfull[i]-mu)

lw.append(0)



sigmalw = 0

for i in lw:
    sigmalw += pow(i, 2)

sigmalw /= lw.__len__() - 1

sigmaup = 0

for i in up:
    sigmaup += pow(i, 2)

sigmaup /= up.__len__() - 1




# SNRLW
x = np.linspace(snrfull[0], mu, 100)
r = stats.norm.pdf(x, mu, sigmalw)
maxval = r[len(r)-1]
min = r[0]
stack.stackplot(x, max(count)*(stats.norm.pdf(x, mu, sigmalw)-min)/(maxval-min), color="blue", alpha=0.3, lw=0)



# SNRUP
x = np.linspace(mu, snrfull[-1], 100)
r = stats.norm.pdf(x, mu, sigmaup)
maxval = r[0]
min = r[len(r)-1]
linedist = stack.stackplot(x, max(count)*(stats.norm.pdf(x, mu, sigmaup)-min)/(maxval-min), color="blue", alpha=0.3, lw=0)
# linedist.set_label("Calculated WSPR distribution")


x = np.array(snr)
y = np.array(count)
line = stack.stackplot(x, y, color="green", alpha=0.3, lw=0)
# line.set_label("WSPR data")



#VOACAP guess
mu = sum(mus)/len(mus)

sigmalw = statistics.median(snrlws)

sigmaup = statistics.median(snrups)


# SNRLW
x = np.linspace(mu-sigmalw, mu, 100)
r = stats.norm.pdf(x, mu, sigmalw)
maxval = r[len(r)-1]
min = r[0]
stack.stackplot(x, max(count)*(stats.norm.pdf(x, mu, sigmalw)-min)/(maxval-min), color="red", alpha=0.3, lw=0)



# SNRUP
x = np.linspace(mu, mu+sigmaup, 100)
r = stats.norm.pdf(x, mu, sigmaup)
maxval = r[0]
min = r[len(r)-1]
linevoacap = stack.stackplot(x, max(count)*(stats.norm.pdf(x, mu, sigmaup)-min)/(maxval-min), color="red", alpha=0.3, lw=0)
# linevoacap.set_label("VOACAP distribution")

stack.set_title("Band " + str(band))
stack.set_ylabel("Count")
stack.set_xlabel("SNR")

stack.legend(['Calculated distribution of WSPR data under median', 'Calculated distribution of WSPR data over median', 'Raw WSPR data', 'VOACAP SNR under median distribution', 'VOACAP SNR over median distribution'])


plt.show()

