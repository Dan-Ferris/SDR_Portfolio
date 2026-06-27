#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <hackrf.h>

// ─── CONFIGURATION ────────────────────────────────────────────
#define SAMPLE_RATE     2000000   // 2 MHz sample rate
#define GAIN            40        // receiver gain
#define NUM_SAMPLES     131072    // samples per capture
#define FREQ_START      88000000  // 88 MHz FM band start
#define FREQ_END        108000000 // 108 MHz FM band end
#define FREQ_STEP       200000    // scan every 200 kHz
#define POWER_THRESHOLD 20.0     // minimum dB to log as signal
// ──────────────────────────────────────────────────────────────

// Global buffer and flag for sample collection
int8_t sample_buffer[NUM_SAMPLES * 2];  // *2 because each sample is I + Q bytes
volatile int samples_ready = 0;          // flag: 1 when buffer is full

int rx_callback(hackrf_transfer* transfer) {
    // Skip if buffer already full
    if (samples_ready != 1) {
        // Copy incoming samples into our global buffer
        memcpy(sample_buffer, transfer->buffer, sizeof(sample_buffer));
        // Signal to main() that samples are ready
        samples_ready = 1;
    }
    return 0;
}

double compute_power(int8_t* buffer, int length) {
    double power = 0.0;
    int samples = length / 2;
    for (int i = 0; i < length; i += 2) {
        double I = buffer[i];
        double Q = buffer[i + 1];
        power += (I * I) + (Q * Q);
    }
    power /= samples;
    return 10.0 * log10(power + 1e-10);
}

int main() {
    // Step 1 — declare device pointer
    hackrf_device* device = NULL;

    // Step 2 — initialize library
    int result = hackrf_init();
    if (result != HACKRF_SUCCESS) {
        printf("Failed to initialize: %s\n", hackrf_error_name(result));
        return 1;
    }

    // Step 3 — open device
    result = hackrf_open(&device);
    if (result != HACKRF_SUCCESS) {
        printf("Failed to open device: %s\n", hackrf_error_name(result));
        hackrf_exit();
        return 1;
    }

    // Step 4 — configure hardware
    hackrf_set_sample_rate(device, SAMPLE_RATE);
    hackrf_set_lna_gain(device, GAIN);
    hackrf_set_vga_gain(device, GAIN / 2);

    printf("HackRF opened successfully!\n");
    printf("Scanning %d MHz to %d MHz...\n\n", FREQ_START/1000000, FREQ_END/1000000);

    FILE* log_file = fopen("/home/adam/SDR_Projects/P3_SIGINT_Scanner/sigint_scan.csv", "w");
    fprintf(log_file, "Frequency (MHz), Power (dB), Timestamp\n");

    // Step 5 — sweep frequency range
    for (uint32_t freq = FREQ_START; freq <= FREQ_END; freq += FREQ_STEP) {
        // Reset buffer flag
        samples_ready = 0;

        // Tune to frequency
        hackrf_set_freq(device, freq);

        // Start receiving
        hackrf_start_rx(device, rx_callback, NULL);

        // Wait for callback to fill buffer
        while (samples_ready == 0) {
            // busy wait
        }

        // Stop receiving
        hackrf_stop_rx(device);

        // Compute signal power
        double power_db = compute_power(sample_buffer, sizeof(sample_buffer));

        if (power_db >= POWER_THRESHOLD) {
            // Print result
            printf("  %.1f MHz  -->  %.2f dB\n", freq/1000000.0, power_db);
            // Log to CSV
            time_t now = time(NULL);
            char timestamp[26];
            strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", localtime(&now));
            fprintf(log_file, "%.1f,%.2f,%s\n", freq/1000000.0, power_db, timestamp);
        }


    }
    
    fclose(log_file);
    printf("results saved to sigint_scan.csv\n");

    // Step 6 — clean up
    hackrf_close(device);
    hackrf_exit();
    printf("\nScan complete!\n");

    return 0;
}