import SoapySDR
from SoapySDR import SOAPY_SDR_CF32, SOAPY_SDR_RX # RX = receive mode, CF32 = complex 32-bit float samples 
import numpy as np
import matplotlib.pyplot as plt

# Open Hackrf
sdr = SoapySDR.Device(dict(driver="hackrf")) # tells soapysdr which device is being used
sdr.setSampleRate(SOAPY_SDR_RX, 0 ,10e6) # 2 mil samples per second
sdr.setFrequency(SOAPY_SDR_RX,0,99.5e6) # 99.5 fm station
sdr.setGain(SOAPY_SDR_RX,0,40) # set gain to 40

#set up stream
stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32) # open pipeline to recieve between hackrf and python 
sdr.activateStream(stream) # start receiving 

#grab samples
buff = np.zeros(4096, dtype=np.complex64) # empty buffer to store 4096 complex IQ samples
sdr.readStream(stream, [buff] ,len(buff)) # fill buffer with real samples from hackrf

#FFT
fft_result = np.fft.fftshift(np.fft.fft(buff)) # run fft and shift so 0 hz is centered
magnitude_db = 20 *np.log10(np.abs(fft_result +1e-10)) # convert result into decibels

#frequency axis centered on tuned freq
freq_axis = np.linspace(99.5-1,99.5+1, len(buff)) # frequency from 98.5 to 105.5 MHz

#plot
plt.figure(figsize=(12,5))
plt.plot(freq_axis, magnitude_db,color="cyan")
plt.fill_between(freq_axis, magnitude_db, -100, alpha=0.3, color="cyan")
plt.title("real FM signal spectrum -99.5 MHZ")
plt.xlabel("Frequency (MHZ)")
plt.ylabel("Power (DB)")
plt.grid(True, alpha=0.3)
plt.ylim(-40,0)
plt.savefig("real_fft.png")
plt.show()
print("plot saved")

