#!/bin/sh

if [ $# -lt 3 ]; then 
    echo "Invalid arg count"
    echo "Usage: ./plotter.sh <band> <tx_sign> <rx_sign>"
    echo "Band values: 10, 14, 7, 21, 24, 28"
    exit 1
fi


# get data from voacap prediction

snr1=$(python voacapextractor.py 1 SNR -f "$1")
snrup1=$(python voacapextractor.py 1 "SNR UP" -f "$1")
snrlw1=$(python voacapextractor.py 1 "SNR LW" -f "$1")

snr2=$(python voacapextractor.py 2 SNR -f "$1")
snrup2=$(python voacapextractor.py 2 "SNR UP" -f "$1")
snrlw2=$(python voacapextractor.py 2 "SNR LW" -f "$1")

snr3=$(python voacapextractor.py 3 SNR -f "$1")
snrup3=$(python voacapextractor.py 3 "SNR UP" -f "$1")
snrlw3=$(python voacapextractor.py 3 "SNR LW" -f "$1")

snr4=$(python voacapextractor.py 4 SNR -f "$1")
snrup4=$(python voacapextractor.py 4 "SNR UP" -f "$1")
snrlw4=$(python voacapextractor.py 4 "SNR LW" -f "$1")

snr5=$(python voacapextractor.py 5 SNR -f "$1")
snrup5=$(python voacapextractor.py 5 "SNR UP" -f "$1")
snrlw5=$(python voacapextractor.py 5 "SNR LW" -f "$1")

snr6=$(python voacapextractor.py 6 SNR -f "$1")
snrup6=$(python voacapextractor.py 6 "SNR UP" -f "$1")
snrlw6=$(python voacapextractor.py 6 "SNR LW" -f "$1")

snr7=$(python voacapextractor.py 7 SNR -f "$1")
snrup7=$(python voacapextractor.py 7 "SNR UP" -f "$1")
snrlw7=$(python voacapextractor.py 7 "SNR LW" -f "$1")

snr8=$(python voacapextractor.py 8 SNR -f "$1")
snrup8=$(python voacapextractor.py 8 "SNR UP" -f "$1")
snrlw8=$(python voacapextractor.py 8 "SNR LW" -f "$1")

snr9=$(python voacapextractor.py 9 SNR -f "$1")
snrup9=$(python voacapextractor.py 9 "SNR UP" -f "$1")
snrlw9=$(python voacapextractor.py 9 "SNR LW" -f "$1")

snr10=$(python voacapextractor.py 10 SNR -f "$1")
snrup10=$(python voacapextractor.py 10 "SNR UP" -f "$1")
snrlw10=$(python voacapextractor.py 10 "SNR LW" -f "$1")

snr11=$(python voacapextractor.py 11 SNR -f "$1")
snrup11=$(python voacapextractor.py 11 "SNR UP" -f "$1")
snrlw11=$(python voacapextractor.py 11 "SNR LW" -f "$1")

snr12=$(python voacapextractor.py 12 SNR -f "$1")
snrup12=$(python voacapextractor.py 12 "SNR UP" -f "$1")
snrlw12=$(python voacapextractor.py 12 "SNR LW" -f "$1")

snr13=$(python voacapextractor.py 13 SNR -f "$1")
snrup13=$(python voacapextractor.py 13 "SNR UP" -f "$1")
snrlw13=$(python voacapextractor.py 13 "SNR LW" -f "$1")

snr14=$(python voacapextractor.py 14 SNR -f "$1")
snrup14=$(python voacapextractor.py 14 "SNR UP" -f "$1")
snrlw14=$(python voacapextractor.py 14 "SNR LW" -f "$1")

snr15=$(python voacapextractor.py 15 SNR -f "$1")
snrup15=$(python voacapextractor.py 15 "SNR UP" -f "$1")
snrlw15=$(python voacapextractor.py 15 "SNR LW" -f "$1")

snr16=$(python voacapextractor.py 16 SNR -f "$1")
snrup16=$(python voacapextractor.py 16 "SNR UP" -f "$1")
snrlw16=$(python voacapextractor.py 16 "SNR LW" -f "$1")

snr17=$(python voacapextractor.py 17 SNR -f "$1")
snrup17=$(python voacapextractor.py 17 "SNR UP" -f "$1")
snrlw17=$(python voacapextractor.py 17 "SNR LW" -f "$1")

snr18=$(python voacapextractor.py 18 SNR -f "$1")
snrup18=$(python voacapextractor.py 18 "SNR UP" -f "$1")
snrlw18=$(python voacapextractor.py 18 "SNR LW" -f "$1")

snr19=$(python voacapextractor.py 19 SNR -f "$1")
snrup19=$(python voacapextractor.py 19 "SNR UP" -f "$1")
snrlw19=$(python voacapextractor.py 19 "SNR LW" -f "$1")

snr20=$(python voacapextractor.py 20 SNR -f "$1")
snrup20=$(python voacapextractor.py 20 "SNR UP" -f "$1")
snrlw20=$(python voacapextractor.py 20 "SNR LW" -f "$1")

snr21=$(python voacapextractor.py 21 SNR -f "$1")
snrup21=$(python voacapextractor.py 21 "SNR UP" -f "$1")
snrlw21=$(python voacapextractor.py 21 "SNR LW" -f "$1")

snr22=$(python voacapextractor.py 22 SNR -f "$1")
snrup22=$(python voacapextractor.py 22 "SNR UP" -f "$1")
snrlw22=$(python voacapextractor.py 22 "SNR LW" -f "$1")

snr23=$(python voacapextractor.py 23 SNR -f "$1")
snrup23=$(python voacapextractor.py 23 "SNR UP" -f "$1")
snrlw23=$(python voacapextractor.py 23 "SNR LW" -f "$1")



python test.py "$1" \
    "$snr1 $snr2 $snr3 $snr4 $snr5 $snr6 $snr7 $snr8 $snr9 $snr10 $snr11 $snr12 $snr13 $snr14 $snr15 $snr16 $snr17 $snr18 $snr19 $snr20 $snr21 $snr22 $snr23" \
    "$snrup1 $snrup2 $snrup3 $snrup4 $snrup5 $snrup6 $snrup7 $snrup8 $snrup9 $snrup10 $snrup11 $snrup12 $snrup13 $snrup14 $snrup15 $snrup16 $snrup17 $snrup18 $snrup19 $snrup20 $snrup21 $snrup22 $snrup23" \
    "$snrlw1 $snrlw2 $snrlw3 $snrlw4 $snrlw5 $snrlw6 $snrlw7 $snrlw8 $snrlw9 $snrlw10 $snrlw11 $snrlw12 $snrlw13 $snrlw14 $snrlw15 $snrlw16 $snrlw17 $snrlw18 $snrlw19 $snrlw20 $snrlw21 $snrlw22 $snrlw23" \
    "$2" \
    "$3"
