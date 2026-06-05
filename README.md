# SDR Portfolio

A collection of Software Defined Radio (SDR) projects built using the HackRF PortaPack H4M, Python, and C. These projects were developed to build practical RF engineering skills for a career in the defense/military field.

## Hardware
- HackRF PortaPack H4M (Mayhem firmware v2.4.0)
- 64GB SanDisk Ultra microSD
- Ubuntu 20.04 (Dell Precision 7770)

## Projects

### 1. FM Signal Strength Logger (Python)
Scans the FM band (87.5–108 MHz), logs signal strength data to CSV, and visualizes the spectrum using Matplotlib.

### 2. Automatic Signal Classifier (Python + GNU Radio)
FFT-based signal detection and classification system that identifies AM, FM, and digital signal types with a live dashboard.

### 3. SIGINT Scanner (C + libhackrf)
Low-level C program that sweeps frequency bands, computes signal power, and logs detections — mirrors real SIGINT system architecture.

### 4. ADS-B Plane Tracker (Python)
Live aircraft tracking system that decodes real ADS-B transmissions at 1090 MHz and plots flight positions on an interactive map.

## Skills Demonstrated
- RF signal processing and spectrum analysis
- Python (NumPy, SoapySDR, Matplotlib)
- C programming with libhackrf
- GNU Radio signal processing pipelines
- Real hardware SDR development