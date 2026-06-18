# Signal Classifier
# Project 2 - SDR Portfolio
# Captures IQ samples, runs FFT, classifies signal as AM, FM, Digital, or Noise

import SoapySDR
from SoapySDR import SOAPY_SDR_CF32, SOAPY_SDR_RX
import numpy as np
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import time

# ─── CONFIGURATION ────────────────────────────────────────────
SAMPLE_RATE     = 2e6       # 2 MHz sample rate
GAIN            = 16        # receiver gain
NUM_SAMPLES     = 65536     # samples per capture
SNR_THRESHOLD   = 10        # minimum SNR to consider a real signal (dB)
BW_FM           = 0.08      # minimum bandwidth to classify as FM (MHz)
BW_DIGITAL      = 0.01      # minimum bandwidth to classify as Digital (MHz)
TARGETS         = [99.5, 97.8]  # frequencies to scan (MHz)
# ──────────────────────────────────────────────────────────────

def setup_sdr(freq_mhz):
    # Open HackRF and tune to target frequency
    try:
        sdr = SoapySDR.Device(dict(driver="hackrf"))
        sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
        sdr.setGain(SOAPY_SDR_RX, 0, GAIN)
        sdr.setFrequency(SOAPY_SDR_RX, 0, freq_mhz * 1e6)
        print(f"HackRF opened — tuned to {freq_mhz} MHz")
        return sdr
    except Exception as e:
        print(f"Error opening HackRF: {e}")
        print("Make sure the HackRF is plugged in and in HackRF mode.")
        return None

def capture_samples(sdr, stream):
    # Capture a block of IQ samples from the HackRF
    try:
        buff = np.zeros(NUM_SAMPLES, dtype=np.complex64)
        sr = sdr.readStream(stream, [buff], len(buff), timeoutUs=5000000)
        if sr.ret <= 0:
            print("Warning: no samples received")
            return None
        return buff
    except Exception as e:
        print(f"Error capturing samples: {e}")
        return None

def compute_fft(samples):
    # Compute FFT and return frequency axis and power in dB
    try:
        fft_result = np.fft.fftshift(np.fft.fft(samples))
        power_db   = 10 * np.log10(np.abs(fft_result)**2 + 1e-10)
        freq_axis  = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/SAMPLE_RATE)) / 1e6
        return freq_axis, power_db
    except Exception as e:
        print(f"Error computing FFT: {e}")
        return None, None

def generate_synthetic_signal(signal_type, duration=0.1):
    # Generate synthetic IQ samples for testing the classifier
    try:
        num_samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, num_samples, dtype=np.float32)

        if signal_type == "FM":
            # FM with 150 kHz deviation to match real FM broadcast bandwidth
            audio  = np.sin(2 * np.pi * 1000 * t)
            phase  = 2 * np.pi * 150000 * np.cumsum(audio) / SAMPLE_RATE
            signal = np.exp(1j * phase).astype(np.complex64)
            noise  = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * 0.1
            return (signal + noise.astype(np.complex64))

        elif signal_type == "AM":
            # AM with 5 kHz audio — narrow bandwidth
            audio     = np.sin(2 * np.pi * 5000 * t)
            carrier   = np.cos(2 * np.pi * 200000 * t)
            am_signal = (1.0 + 0.9 * audio) * carrier
            noise     = np.random.randn(num_samples) * 0.1
            iq        = (am_signal + noise).astype(np.complex64)
            return iq + 0j

        elif signal_type == "DIGITAL":
            # BPSK with 50 kHz symbol rate
            bits    = np.random.randint(0, 2, num_samples // 40)
            symbols = (2 * bits - 1).astype(np.float32)
            signal  = np.repeat(symbols, 40)[:num_samples]
            carrier = np.exp(1j * 2 * np.pi * 200000 * t)
            noise   = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * 0.1
            iq      = (signal * carrier).astype(np.complex64) + noise.astype(np.complex64)
            return iq

        else:
            # Pure noise
            noise = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * 0.05
            return noise.astype(np.complex64)

    except Exception as e:
        print(f"Error generating synthetic {signal_type} signal: {e}")
        return None

def classify_signal(freq_axis, power_db):
    # Classify signal based on bandwidth after removing DC spike
    try:
        # Remove DC spike — HackRF hardware artifact at center frequency
        center   = len(power_db) // 2
        power_db = power_db.copy()
        power_db[center - 5 : center + 5] = np.percentile(power_db, 50)

        # Basic stats
        noise_floor = np.percentile(power_db, 20)
        peak_power  = np.max(power_db)
        snr         = peak_power - noise_floor

        # No real signal present
        if snr < SNR_THRESHOLD:
            return "NOISE", 0.0, noise_floor

        # Measure bandwidth at -6 dB from peak
        threshold     = peak_power - 6
        above         = power_db > threshold
        signal_bins   = np.sum(above)
        bin_width_mhz = (freq_axis[-1] - freq_axis[0]) / len(freq_axis)
        bandwidth_mhz = signal_bins * bin_width_mhz

        # Classify by bandwidth
        # FM broadcast = 150-200 kHz wide
        # Digital = 10-100 kHz wide
        # AM = under 10 kHz wide
        if bandwidth_mhz > BW_FM:
            return "FM", bandwidth_mhz, noise_floor
        elif bandwidth_mhz > BW_DIGITAL:
            return "DIGITAL", bandwidth_mhz, noise_floor
        else:
            return "AM", bandwidth_mhz, noise_floor

    except Exception as e:
        print(f"Error classifying signal: {e}")
        return "UNKNOWN", 0.0, 0.0

def log_result(freq_mhz, classification, bandwidth, noise_floor):
    # Log classification result to CSV
    try:
        filename    = "classifications.csv"
        file_exists = False
        try:
            with open(filename, 'r'):
                file_exists = True
        except FileNotFoundError:
            pass

        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Frequency (MHz)",
                                 "Classification", "Bandwidth (MHz)", "Noise Floor (dB)"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                round(freq_mhz, 1),
                classification,
                round(bandwidth, 4),
                round(noise_floor, 2)
            ])
    except Exception as e:
        print(f"Error logging result: {e}")

def plot_result(freq_axis, power_db, freq_mhz, classification, bandwidth):
    # Plot the spectrum with classification result
    try:
        plt.figure(figsize=(12, 5))
        plt.plot(freq_axis, power_db, color="cyan", linewidth=1.0)
        plt.fill_between(freq_axis, power_db, min(power_db), alpha=0.3, color="cyan")

        noise_floor = np.percentile(power_db, 10)
        plt.axhline(y=noise_floor, color='red', linestyle='--', linewidth=1,
                    label=f'Noise Floor ({noise_floor:.1f} dB)')

        plt.title(f"{freq_mhz} MHz — Classified as: {classification} "
                  f"(BW: {bandwidth:.3f} MHz)")
        plt.xlabel("Frequency offset (MHz)")
        plt.ylabel("Power (dB)")
        plt.legend(loc='upper right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"classification_{str(freq_mhz).replace('.', '_')}MHz.png", dpi=150)
        plt.show()

    except Exception as e:
        print(f"Error plotting result: {e}")

def run_synthetic_tests():
    # Test the classifier against known synthetic signals
    # Note: synthetic signals are centered at 0 Hz so DC removal affects them
    # differently than real hardware signals — this is a known limitation
    print("\n" + "="*50)
    print("SYNTHETIC SIGNAL VALIDATION")
    print("="*50)

    test_cases = ["FM", "AM", "DIGITAL", "NOISE"]

    for signal_type in test_cases:
        try:
            print(f"\nGenerating synthetic {signal_type} signal...")
            samples = generate_synthetic_signal(signal_type)

            if samples is None:
                print(f"  Skipping {signal_type} — signal generation failed")
                continue

            freq_axis, power_db = compute_fft(samples)
            if freq_axis is None:
                print(f"  Skipping {signal_type} — FFT failed")
                continue

            classification, bandwidth, noise_floor = classify_signal(freq_axis, power_db)
            correct = "✓ CORRECT" if classification == signal_type else f"✗ GOT {classification}"

            print(f"  Expected:    {signal_type}")
            print(f"  Result:      {classification} — {correct}")
            print(f"  Bandwidth:   {bandwidth:.3f} MHz")
            print(f"  Noise Floor: {noise_floor:.2f} dB")

            log_result(0.0, f"SYNTHETIC_{classification}", bandwidth, noise_floor)
            plot_result(freq_axis, power_db, 0.0,
                        f"SYNTHETIC {signal_type} -> {classification}", bandwidth)

        except Exception as e:
            print(f"  Error testing {signal_type}: {e}")
            continue

def main():
    sdr = setup_sdr(TARGETS[0])
    if sdr is None:
        return

    stream = None
    try:
        stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        sdr.activateStream(stream)

        for freq in TARGETS:
            print(f"\nAnalyzing {freq} MHz...")
            sdr.setFrequency(SOAPY_SDR_RX, 0, freq * 1e6)

            # Use higher gain for non-FM frequencies
            if freq < 87.5 or freq > 108.0:
                sdr.setGain(SOAPY_SDR_RX, 0, 40)
            else:
                sdr.setGain(SOAPY_SDR_RX, 0, GAIN)

            time.sleep(0.5)

            samples = capture_samples(sdr, stream)
            if samples is None:
                continue

            freq_axis, power_db = compute_fft(samples)
            if freq_axis is None:
                continue

            classification, bandwidth, noise_floor = classify_signal(freq_axis, power_db)

            print(f"  Result:      {classification}")
            print(f"  Bandwidth:   {bandwidth:.3f} MHz")
            print(f"  Noise Floor: {noise_floor:.2f} dB")

            log_result(freq, classification, bandwidth, noise_floor)
            plot_result(freq_axis, power_db, freq, classification, bandwidth)

    except Exception as e:
        print(f"Error during scan: {e}")

    finally:
        if stream is not None:
            sdr.deactivateStream(stream)
            sdr.closeStream(stream)
            print("\nHackRF closed cleanly.")

    # Run synthetic validation tests
    run_synthetic_tests()

if __name__ == "__main__":
    main()