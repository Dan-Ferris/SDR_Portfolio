import numpy as np
import matplotlib.pyplot as plt

#simulate two signals mixed together 
# signal 1: 1000hz, signal 2 2500hz
sample_rate = 1000
t = np.linspace(0,1,sample_rate)

signal1 = np.sin(2 *np.pi * 1000 * t) #1000hz
signal2 = np.sin(2 *np.pi * 2500 * t) #2500hz
combined = signal1 + signal2

#plot time domain
plt.figure(figsize=(12,8))

plt.subplot(2,1,1)
plt.plot(t[:200], combined[:200])

plt.title("time domain - hard to see individual frequencies")
plt.xlabel("time (S)")
plt.ylabel("Ampltidue ")
plt.grid(True)

# compute FFt
fft_result = np.fft.fft(combined)
frequencies = np.fft.fftfreq(len(combined) , 1/sample_rate)
magnitude = np.abs(fft_result)

#plot frequency domain
plt.subplot(2,1,2)
plt.plot(frequencies[:sample_rate//2], magnitude[:sample_rate//2])
plt.title("frequency domain (FFT) - clear peaks at 100hz and 2500hz")
plt.xlabel("frequency (hz)")
plt.ylabel("magnitude")
plt.grid(True)

plt.tight_layout()
plt.savefig("fft_demo.png")
plt.show() 
print("plot saves as fft_demo.png")