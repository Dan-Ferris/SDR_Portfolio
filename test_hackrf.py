import SoapySDR 
from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
import numpy as np 

#find and print all connected SDR devices
results = SoapySDR.Device.enumerate()
print("found devices:")
for result in results:
    print(" ",result)


#open the HackRF
sdr = SoapySDR.Device(dict(driver="hackrf"))

#configure it
sdr.setSampleRate(SOAPY_SDR_RX, 0, 2e6) #2 MHz sample rate
sdr.setFrequency(SOAPY_SDR_RX, 0, 100.1e6)    #100.1 Mhz FM radio
sdr.setGain(SOAPY_SDR_RX, 0 ,40) # gain

#set up the receive stream
stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(stream)

#receive 1024 samples
buff = np.zeros(1024,dtype=np.complex64)
sr = sdr.readStream(stream, [buff], len(buff))

print(f"recieved {sr.ret} samples")
print(f"first 5 samples: {buff[:5]}")

#compute signal power
power = np.mean(np.abs(buff)**2)
print(f"signal power: {power:.6f}")

#clean up 
sdr.deactivateStream(stream)
sdr.closeStream(stream)


