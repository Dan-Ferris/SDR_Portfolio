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
SAMPLE_RATE = 2e6    # 2 MHz sample rate
GAIN        = 40     # receiver gain
NUM_SAMPLES = 4096   # samples per measurement
STEP        = 0.2    # scan every 0.2 MHz
FM_START    = 87.5   # FM band start (MHz)
FM_END      = 108.0  # FM band end (MHz)
# ──────────────────────────────────────────────────────────────

def setup_sdr():
    # Open HackRF and configure it — crash early with a clear message if not found
    try:
        sdr = SoapySDR.Device(dict(driver="hackrf"))
        sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
        sdr.setGain(SOAPY_SDR_RX, 0, GAIN)
        print("HackRF opened successfully!")
        return sdr
    except Exception as e:
        print(f"Error opening HackRF: {e}")
        print("Make sure the HackRF is plugged in and in HackRF mode.")
        return None

def measure_power(sdr, stream, freq_mhz):
    # Tune to frequency and measure signal power
    try:
        sdr.setFrequency(SOAPY_SDR_RX, 0, freq_mhz * 1e6)
        time.sleep(0.05)  # let tuner settle

        # Grab samples with 1 second timeout
        buff = np.zeros(NUM_SAMPLES, dtype=np.complex64)
        sr = sdr.readStream(stream, [buff], len(buff), timeoutUs=1000000)

        # Check if we actually got samples
        if sr.ret <= 0:
            print(f"  Warning: no samples received at {freq_mhz:.1f} MHz")
            return None

        # Compute power in dB
        power = np.mean(np.abs(buff) ** 2)
        power_db = 10 * np.log10(power + 1e-10)
        return power_db

    except Exception as e:
        print(f"  Error measuring {freq_mhz:.1f} MHz: {e}")
        return None

def scan_fm_band(sdr, stream):
    # Scan every frequency in the FM band
    frequencies = np.arange(FM_START, FM_END, STEP)
    results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\nScanning FM band {FM_START}–{FM_END} MHz...\n")

    for freq in frequencies:
        power_db = measure_power(sdr, stream, freq)

        # Skip this frequency if measurement failed
        if power_db is None:
            continue

        results.append((freq, power_db, timestamp))
        print(f"    {freq:.1f} MHz  -->  {power_db:.2f} dB")

    return results

def save_to_csv(results):
    # Save scan results to CSV file with timestamp in name
    try:
        filename = f"fm_scan_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Frequency (MHz)", "Power (dB)", "Timestamp"])
            for freq, power, ts in results:
                writer.writerow([round(freq, 1), round(power, 2), ts])

        # These two lines were inside the with block before — now correctly outside
        print(f"\nData saved to {filename}")
        return filename

    except Exception as e:
        print(f"Error saving CSV: {e}")
        return None

def plot_spectrum(results):
    # Plot the full FM band spectrum
    try:
        freqs  = [r[0] for r in results]
        powers = [r[1] for r in results]

        plt.figure(figsize=(14, 6))
        plt.plot(freqs, powers, color="cyan", linewidth=1.5)
        plt.fill_between(freqs, powers, min(powers), alpha=0.3, color="cyan")

        # Mark strongest stations
        top5 = sorted(results, key=lambda x: x[1], reverse=True)[:5]
        for freq, power, _ in top5:
            plt.annotate(f"{freq:.1f}", xy=(freq, power),
                         xytext=(0, 10), textcoords="offset points",
                         ha="center", fontsize=8, color="yellow")
            plt.plot(freq, power, "yo", markersize=6)

        plt.title(f"FM Band Spectrum Scan - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        plt.xlabel("Frequency (MHz)")
        plt.ylabel("Signal Power (dB)")
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

        # Scan the FM band
        results = scan_fm_band(sdr, stream)

    except Exception as e:
        print(f"Error during scan: {e}")
        results = []

    finally:
        # Always clean up hardware even if something crashes
        if stream is not None:
            sdr.deactivateStream(stream)
            sdr.closeStream(stream)
            print("HackRF closed cleanly.")

    # Only save and plot if we got data
    if not results:
        print("No data collected. Exiting.")
        return

    # Save to CSV
    save_to_csv(results)

    # Print top 5 stations
    print("\nTop 5 strongest stations:")
    top5 = sorted(results, key=lambda x: x[1], reverse=True)[:5]
    for freq, power, _ in top5:
        print(f"    {freq:.1f} MHz  -->  {power:.2f} dB")

    # Plot spectrum
    plot_spectrum(results)

if __name__ == "__main__":
    main()