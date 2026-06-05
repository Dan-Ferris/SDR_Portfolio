import SoapySDR
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
import numpy as np 
import time
import csv
from datetime import datetime
 
#open the HackRF
sdr = SoapySDR.Device(dict(driver="hackrf"))

#configure it
sdr.setSampleRate(SOAPY_SDR_RX, 0, 2e6) #2 MHz sample rate
sdr.setGain(SOAPY_SDR_RX, 0 ,40) # gain

#set up the receive stream
stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(stream)

# FM stations to scan 
stations = [88.5,90.1,91.9,93.3,95.5,97.1,99.5,101.1,103.5,105.7,107.3]

print("\n")

print(f"Scanning FM stations.....\n")
print(f"{'station':<12} {'Power (dB)':<15}'{'Signal'}")

results = []

for freq in stations:
    #tune to frequency
    sdr.setFrequency(SOAPY_SDR_RX,0,freq*1e6)
    time.sleep(0.1) #let it settle

    #grab samples
    buff = np.zeros(1024,dtype=np.complex64)
    sr = sdr.readStream(stream, [buff], len(buff))

    #compute power in dB
    power = np.mean(np.abs(buff)**2)
    power_db = 10 *np.log10(power +1e-10)

    #simple signal indicator
    if power_db > -30:
        signal = "|||||||||||||| STRONG"
    elif power_db >-50:
        signal = "||||||||       MEDIUM"
    else:
        signal=  "|||            WEAK"
    
    print(f"{freq:<12} {power_db:<15.2f} {signal}")
    results.append((freq,power_db))

#clean up 
sdr.deactivateStream(stream)
sdr.closeStream(stream)

#print top 3 strongest stations
print("\nTop 3 strongest stations:")
top3=sorted(results,key=lambda x: x[1], reverse=True)[:3]
for freq,power in top3:
    print(f" {freq} Mhz - {power:.2f} dB")

#save to csv
filename = f"fm_scan_{datetime.now().strftime('%Y%m%d_%H%M%s')}.csv"
with open(filename, "w", newline=" ") as f:
    writer = csv.writer(f)
    writer.writerow(["frequency (MHZ) , power (db), timestamp"])
    for freq,power in results:
        writer.writerow([freq, round(power,2), datetime.now().strftime('%Y%m%d_%H%M%s')])

    print(f"\nresults saved to {filename}")