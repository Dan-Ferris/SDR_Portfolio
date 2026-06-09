import SoapySDR
from SoapySDR import SOAPY_SDR_CF32, SOAPY_SDR_RX 
import numpy as np

print("Opening HackRF...")
sdr = SoapySDR.Device(dict(driver="hackrf"))
print("HackRf opened")

print("Setting sample rate...")
sdr.setSampleRate(SOAPY_SDR_RX, 0, 2e6)
print("done")

print("setting frequency...")
sdr.setFrequency(SOAPY_SDR_RX, 0 ,99.5e6)
print("DONE")

print("setting up stream")
stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
print("done")

print("ACTIVATING STREAM")
sdr.activateStream(stream)
print("done")

print("reading sample...")
buff = np.zeros(1024, dtype=np.complex64)
sr = sdr.readStream(stream, [buff], len(buff), timeoutUs=1000000)
print(f"got {sr.ret} samples")

sdr.deactivateStream(stream)
sdr.closeStream(stream)
print("alldone")