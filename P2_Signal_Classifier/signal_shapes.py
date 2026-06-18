import numpy as np
import matplotlib.pyplot as plt

SAMPLE_RATE = 2e6
t = np.linspace(0, 0.1, int(SAMPLE_RATE * 0.1), dtype=np.float32)

# ── FM Signal ──
audio  = np.sin(2 * np.pi * 1000 * t)
phase  = 2 * np.pi * 75000 * np.cumsum(audio) / SAMPLE_RATE
fm     = np.exp(1j * phase).astype(np.complex64)

# ── AM Signal ──
audio  = np.sin(2 * np.pi * 1000 * t)
am     = ((1 + 0.5 * audio) * np.cos(2 * np.pi * 100000 * t)).astype(np.complex64)

# ── Digital Signal ──
bits     = np.random.randint(0, 2, len(t) // 10)
symbols  = 2 * bits - 1
signal   = np.repeat(symbols, 10)[:len(t)]
digital  = np.exp(1j * np.pi * signal).astype(np.complex64)

# ── Noise ──
noise = (np.random.randn(len(t)) + 1j * np.random.randn(len(t))).astype(np.complex64)

# ── Plot all 4 ──
fig, axes = plt.subplots(4, 1, figsize=(12, 14))
signals = [("FM", fm), ("AM", am), ("DIGITAL", digital), ("NOISE", noise)]

for ax, (name, sig) in zip(axes, signals):
    fft    = np.fft.fftshift(np.fft.fft(sig))
    power  = 10 * np.log10(np.abs(fft)**2 + 1e-10)
    freqs  = np.fft.fftshift(np.fft.fftfreq(len(sig), 1/SAMPLE_RATE)) / 1e6
    ax.plot(freqs, power, color="cyan", linewidth=0.8)
    ax.fill_between(freqs, power, min(power), alpha=0.3, color="cyan")
    ax.set_title(f"{name} Signal", fontsize=12)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Power (dB)")
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("signal_shapes.png", dpi=150)
plt.show()