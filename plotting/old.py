import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import psycopg2
import scipy.stats as stats
import statistics
import math
import argparse



parser = argparse.ArgumentParser("WSPRcomp")
_ = parser.add_argument("hour", help="The hour that will be fetched (+-30 minutes)")
_ = parser.add_argument("frequency", help="The frequency that will be fetched")
_ = parser.add_argument("snr", help="Expected SNR")
_ = parser.add_argument("snrup", help="90 percentile expected SNR")
_ = parser.add_argument("snrlw", help="10th percentile expected SNR")
args = parser.parse_args()




host = "172.17.0.2"
user = "postgres"
db = "postgres"

conn = psycopg2.connect(dbname=db, user=user, host=host)
c = conn.cursor()

band = args.frequency.split(".")[0]
H = int(args.hour)
# query = "SELECT COUNT(snr), snr FROM wspr.rx WHERE " + "band = " + band + " AND (EXTRACT(HOUR FROM time) = " + str(H-1) + " AND EXTRACT(MINUTE FROM time) > 30" +" OR (EXTRACT(HOUR FROM time) = " + str(H) + " AND EXTRACT(MINUTE FROM time) < 30)) GROUP BY snr ORDER BY snr DESC;"
query = "SELECT COUNT(snr), snr FROM wspr.rx WHERE " + "band = " + band + " AND (EXTRACT(HOUR FROM time) < " + str(H) + " AND EXTRACT(HOUR FROM time) > " + str(H-1) + " GROUP BY snr ORDER BY snr DESC;"
# Grabs snr values +-30 mins around H
c.execute(query)


snr: list[int] = list()
count: list[int] = list()


for res in c:
    snr.append(res[1])
    count.append(res[0])

# query = "SELECT snr FROM wspr.rx WHERE " + "band = " + band + " AND (EXTRACT(HOUR FROM time) = " + str(H-1) + " AND EXTRACT(MINUTE FROM time) > 30" +" OR (EXTRACT(HOUR FROM time) = " + str(H) + " AND EXTRACT(MINUTE FROM time) < 30)) ORDER BY snr DESC;"
query = "SELECT snr FROM wspr.rx WHERE " + "band = " + band + " AND (EXTRACT(HOUR FROM time) < " + str(H) + " AND EXTRACT(HOUR FROM time) > " + str(H-1) + " ORDER BY snr DESC;"
c.execute(query)

snrfull: list[int] = list()
for res in c:
    snrfull.append(res[0])

c.close()
conn.close()

assert all(isinstance(i, int) for i in snr)
assert all(isinstance(i, int) for i in count)


x = np.array(snr)
y = np.array(count)
fix, ax = plt.subplots()
ax.plot(x, y, color="green")









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
ax.plot(x, max(count)*(stats.norm.pdf(x, mu, sigmalw)-min)/(maxval-min), color="blue")



# SNRUP
x = np.linspace(mu, snrfull[-1], 100)
r = stats.norm.pdf(x, mu, sigmaup)
maxval = r[0]
min = r[len(r)-1]
ax.plot(x, max(count)*(stats.norm.pdf(x, mu, sigmaup)-min)/(maxval-min), color="blue")


print(sigmaup)
print(sigmalw)



#VOACAP guess
mu = float(args.snr) - 32

sigmalw = (mu-float(args.snrlw))/1.28
if sigmalw < 0: sigmalw = -sigmalw

sigmaup = (mu+float(args.snrup))/1.28
if sigmaup < 0: sigmaup = -sigmaup


print(sigmaup)
print(sigmalw)
print(mu)

# SNRLW
x = np.linspace(mu-sigmalw, mu, 100)
r = stats.norm.pdf(x, mu, sigmalw)
maxval = r[len(r)-1]
min = r[0]
ax.plot(x, max(count)*(stats.norm.pdf(x, mu, sigmalw)-min)/(maxval-min), color="red")



# SNRUP
x = np.linspace(mu, mu+sigmaup, 100)
r = stats.norm.pdf(x, mu, sigmaup)
maxval = r[0]
min = r[len(r)-1]
ax.plot(x, max(count)*(stats.norm.pdf(x, mu, sigmaup)-min)/(maxval-min), color="red")






plt.show()
