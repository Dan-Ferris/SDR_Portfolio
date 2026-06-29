# Project 3 — SIGINT Scanner

A low-level C program that sweeps the FM band using a HackRF One, computes 
FFT-based signal power per frequency, and logs detections above a configurable 
threshold to CSV. Written using libhackrf directly — no abstraction layers.

## How It Works

1. Initializes libhackrf and opens the HackRF device
2. Configures sample rate (2 MHz) and gain settings
3. Sweeps from 88.1 MHz to 108.0 MHz in 200 kHz steps (odd frequencies 
   aligned to US FM channel assignments)
4. At each frequency:
   - Starts receiving via callback function
   - Waits for buffer to fill (with timeout failsafe)
   - Runs FFT using FFTW3 on 131,072 IQ samples
   - Measures power in center ±200 kHz window (matching FM channel bandwidth)
   - Logs detections above threshold to CSV with timestamp
5. Cleans up hardware and exits

## Key Technical Details

**FFT-based power measurement** — unlike simple total power averaging, this 
implementation uses FFTW3 to compute the frequency spectrum and measures power 
only within a 200 kHz window centered on the target frequency. This eliminates 
adjacent channel interference and gives accurate per-station signal strength.

**Callback architecture** — libhackrf delivers samples via an asynchronous 
callback function running on a separate thread. A volatile flag and global buffer 
coordinate between the callback thread and main, a standard pattern in embedded 
and real-time systems.

**Frequency resolution** — with 131,072 samples at 2 MHz sample rate, each FFT 
bin represents ~15.3 Hz. The 200 kHz measurement window covers ~13,000 bins.

## Configuration

All parameters are defined at the top of `sigint_scanner.c`:

| Constant | Default | Description |
|---|---|---|
| SAMPLE_RATE | 2,000,000 | Samples per second |
| GAIN | 40 | LNA gain (dB) |
| NUM_SAMPLES | 131,072 | Samples per capture |
| FREQ_START | 88,100,000 | Start frequency (Hz) |
| FREQ_END | 108,000,000 | End frequency (Hz) |
| FREQ_STEP | 200,000 | Step size (Hz) |
| POWER_THRESHOLD | -32.0 | Minimum dB to log |
| TIMEOUT_LIMIT | 1,000,000 | Busy wait timeout |

## Example Output

HackRF opened successfully

Scanning 88.1 MHz to 108.0 MHz...

105.7 MHz  -->  -26.89 dB

105.9 MHz  -->  -28.58 dB

107.5 MHz  -->  -28.09 dB

107.7 MHz  -->  -26.27 dB

Results saved to sigint_scan.csv

Scan complete

## Build

```bash
gcc sigint_scanner.c -o sigint_scanner \
    -I/usr/include/libhackrf \
    -lhackrf -lm -lfftw3
```

## Requirements

- HackRF One / PortaPack H4M (in HackRF mode)
- libhackrf-dev
- libfftw3-dev
- Ubuntu 20.04 / Linux

## Key Concepts Demonstrated

- Direct hardware interfacing in C using libhackrf
- Asynchronous callback architecture with volatile shared state
- FFT-based signal processing using FFTW3
- Bandwidth-limited power measurement (200 kHz window)
- Error handling and hardware failsafes in C
- CSV data logging with timestamps