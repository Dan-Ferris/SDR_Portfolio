import SoapySDR
from SoapySDR import SOAPY_SDR_CF32, SOAPY_SDR_RX
import numpy as np
import matplotlib.pyplot as plt

# Open Hackrf
sdr = SoapySDR.Device(dict(driver="hackrf"))
sdr.setSampleRate(SOAPY_SDR_RX, 0 ,2e6)
sdr.setFrequency(SOAPY_SDR_RX,0,99.5e6)
sdr.setGain(SOAPY_SDR_RX,0,40)

#set up stream
stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(stream)

#grab samples
buff = np.zeros(4096, dtype=np.complex64)
sdr.readStream(stream, [buff] ,len(buff))

#FFT
fft_result = np.fft.fftshift(np.fft.fft(buff))
magnitude_db = 20 *np.log10(np.abs(fft_result +1e-10))

#frequency axis centered on tuned freq
freq_axis = np.linspace(99.5-1,99.5+1, len(buff))

#plot
plt.figure(figsize=(12,5))
plt.plot(freq_axis, magnitude_db,color="cyan")
plt.fill_between(freq_axis, magnitude_db, -100, alpha=0.3, color="cyan")
plt.title("real FM signal spectrum -99.5 MHZ")
plt.xlabel("Frequency (MHZ)")
plt.ylabel("Power (DB)")
plt.grid(True, alpha=0.3)
plt.ylim(-100,0)
plt.savefig("real_fft.png")
plt.show()
print("plot saved")

