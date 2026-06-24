import numpy as np
import matplotlib.pyplot as plt

# Read the raw IQ file saved by GNU Radio
iq_data = np.fromfile('/home/adam/iq_recording.bin', dtype=np.complex64)

print(f"Loaded {len(iq_data)} IQ samples")

# Compute FFT
fft_result  = np.fft.fftshift(np.fft.fft(iq_data[:65536]))
power_db    = 10 * np.log10(np.abs(fft_result)**2 + 1e-10)

# Frequency axis — centered on 100.3 MHz, 2 MHz wide
freq_axis = np.linspace(100.3 - 1, 100.3 + 1, 65536)

# Plot
plt.figure(figsize=(12, 5))
plt.plot(freq_axis, power_db, color='cyan', linewidth=0.8)
plt.fill_between(freq_axis, power_db, min(power_db), alpha=0.3, color='cyan')
plt.title('Recorded IQ File — 100.3 MHz FM Station')
plt.xlabel('Frequency (MHz)')
plt.ylabel('Power (dB)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('iq_recording_spectrum.png', dpi=150)
plt.show()
print("Done!")