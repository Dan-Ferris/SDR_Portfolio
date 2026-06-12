# FM Signal Strength Logger
# Project 1 - SDR Portfolio
# Scans full FM band, logs signal strength to CSV, plots spectrum

import SoapySDR
from SoapySDR import SOAPY_SDR_CF32, SOAPY_SDR_RX
import numpy as np
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import time

# ─── CONFIGURATION ────────────────────────────────────────────
GAIN     = 16      # receiver gain
FM_START = 87.5    # FM band start (MHz)
FM_END   = 108.0   # FM band end (MHz)
# ──────────────────────────────────────────────────────────────

def setup_sdr():
    # Open HackRF and configure it — exit early with clear message if not found
    try:
        sdr = SoapySDR.Device(dict(driver="hackrf"))
        sdr.setSampleRate(SOAPY_SDR_RX, 0, 2e6)
        sdr.setGain(SOAPY_SDR_RX, 0, GAIN)
        print("HackRF opened successfully!")
        return sdr
    except Exception as e:
        print(f"Error opening HackRF: {e}")
        print("Make sure the HackRF is plugged in and in HackRF mode.")
        return None

def scan_fm_band_fft(sdr, stream):
    # Tune to center of FM band and capture the whole band in one FFT
    center_freq = (FM_START + FM_END) / 2  # 97.75 MHz center

    # Use 10 MHz sample rate to see more of the band at once
    sdr.setSampleRate(SOAPY_SDR_RX, 0, 10e6)
    sdr.setFrequency(SOAPY_SDR_RX, 0, center_freq * 1e6)
    sdr.setGain(SOAPY_SDR_RX, 0, GAIN)
    time.sleep(0.1)

    print(f"\nCapturing FM band {FM_START}–{FM_END} MHz...\n")

    # Grab a large buffer for better frequency resolution
    num_samples = 65536
    buff = np.zeros(num_samples, dtype=np.complex64)
    sr = sdr.readStream(stream, [buff], len(buff), timeoutUs=2000000)

    if sr.ret <= 0:
        print("Error: no samples received")
        return []

    print(f"Captured {sr.ret} samples — computing FFT...")

    # Compute FFT and convert to dB
    fft_result = np.fft.fftshift(np.fft.fft(buff))
    magnitude_db = 10 * np.log10(np.abs(fft_result)**2 + 1e-10)

    # Build frequency axis centered on our tuned frequency (+/- 5 MHz)
    freq_axis = np.linspace(center_freq - 5, center_freq + 5, num_samples)

    # Filter to FM band only and build results list
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []
    for i, freq in enumerate(freq_axis):
        if FM_START <= freq <= FM_END:
            results.append((freq, magnitude_db[i], timestamp))

    print(f"Done — {len(results)} frequency points collected.")
    return results

def save_to_csv(results):
    # Save scan results to CSV file with timestamp in name
    try:
        filename = f"fm_scan_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Frequency (MHz)", "Power (dB)", "Timestamp"])
            for freq, power, ts in results:
                writer.writerow([round(freq, 4), round(power, 2), ts])

        print(f"\nData saved to {filename}")
        return filename

    except Exception as e:
        print(f"Error saving CSV: {e}")
        return None

def get_top_stations(results, n=5):
    # Deduplicate by rounding to nearest 0.1 MHz then return top n by power
    seen = set()
    unique_results = []
    for freq, power, ts in results:
        rounded = round(freq, 1)
        if rounded not in seen:
            seen.add(rounded)
            unique_results.append((rounded, power, ts))

    return sorted(unique_results, key=lambda x: x[1], reverse=True)[:n]

def plot_spectrum(results, top5):
    # Plot the full FM band spectrum
    try:
        freqs  = [r[0] for r in results]
        powers = [r[1] for r in results]

        plt.figure(figsize=(14, 6))
        plt.plot(freqs, powers, color="cyan", linewidth=1.0)
        plt.fill_between(freqs, powers, min(powers), alpha=0.3, color="cyan")

        # Draw noise floor line at 10th percentile
        noise_floor = np.percentile(powers, 10)
        plt.axhline(y=noise_floor, color='red', linestyle='--', linewidth=1,
                    label=f'Noise Floor ({noise_floor:.1f} dB)')

        # Mark top 5 strongest stations
        for freq, power, _ in top5:
            plt.annotate(f"{freq:.1f}", xy=(freq, power),
                         xytext=(0, 10), textcoords="offset points",
                         ha="center", fontsize=8, color="yellow")
            plt.plot(freq, power, "yo", markersize=6)

        plt.title(f"FM Band Spectrum Scan - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        plt.xlabel("Frequency (MHz)")
        plt.ylabel("Signal Power (dB)")
        plt.legend(loc='upper right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("fm_spectrum.png", dpi=150)
        plt.show()
        print("Spectrum plot saved as fm_spectrum.png")

    except Exception as e:
        print(f"Error plotting spectrum: {e}")

def main():
    # Set up SDR — exit early if device not found
    sdr = setup_sdr()
    if sdr is None:
        return

    stream = None
    try:
        stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        sdr.activateStream(stream)

        # Capture FM band via FFT
        results = scan_fm_band_fft(sdr, stream)

    except Exception as e:
        print(f"Error during scan: {e}")
        results = []

    finally:
        # Always clean up hardware even if something crashes
        if stream is not None:
            sdr.deactivateStream(stream)
            sdr.closeStream(stream)
            print("HackRF closed cleanly.")

    # Exit if no data collected
    if not results:
        print("No data collected. Exiting.")
        return

    # Save to CSV
    save_to_csv(results)

    # Get top 5 unique stations
    top5 = get_top_stations(results)

    # Print top 5
    print("\nTop 5 strongest stations:")
    for freq, power, _ in top5:
        print(f"    {freq:.1f} MHz  -->  {power:.2f} dB")

    # Plot spectrum with top 5 marked
    plot_spectrum(results, top5)

if __name__ == "__main__":
    main()