#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <hackrf.h>
#include <fftw3.h>

// ─── CONFIGURATION ────────────────────────────────────────────
#define SAMPLE_RATE     2000000   // 2 MHz sample rate
#define GAIN            40        // receiver gain
#define NUM_SAMPLES     131072    // samples per capture
#define FREQ_START      88100000  // 88 MHz FM band start
#define FREQ_END        108000000 // 108 MHz FM band end
#define FREQ_STEP       200000    // scan every 200 kHz
#define POWER_THRESHOLD -32.0     // minimum dB to log as signal
#define TIMEOUT_LIMIT   1000000   // max iterations before timeout
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
    int num_samples = length / 2;

    // Allocate FFTW input and output arrays
    fftw_complex* in  = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * num_samples);
    fftw_complex* out = (fftw_complex*) fftw_malloc(sizeof(fftw_complex) * num_samples);

    if (in == NULL || out == NULL) {
        printf("Error: failed to allocate FFT buffers\n");
        if (in)  fftw_free(in);
        if (out) fftw_free(out);
        return -100.0;
    }

    // Convert raw int8 IQ samples to complex doubles
    for (int i = 0; i < num_samples; i++) {
        in[i][0] = buffer[i * 2];       // I component (real)
        in[i][1] = buffer[i * 2 + 1];   // Q component (imaginary)
    }

    // Create and execute FFT plan
    fftw_plan plan = fftw_plan_dft_1d(num_samples, in, out, FFTW_FORWARD, FFTW_ESTIMATE);
    fftw_execute(plan);

    // Only measure power in center 10% of bins — target frequency band
    int center     = num_samples / 2;
    int window     = num_samples / 10;  // 10% of bins around center
    double power   = 0.0;

    for (int i = center - window; i < center + window; i++) {
        double real = out[i][0];
        double imag = out[i][1];
        power += (real * real) + (imag * imag);
    }
    power /= (2 * window) * (double)num_samples * (double)num_samples;

    // Clean up
    fftw_destroy_plan(plan);
    fftw_free(in);
    fftw_free(out);

    return 10.0 * log10(power + 1e-10);
}

// Helper function — cleans up and exits with error code
void cleanup_and_exit(hackrf_device* device, FILE* log_file, int code) {
    if (log_file != NULL) fclose(log_file);
    if (device != NULL) {
        hackrf_stop_rx(device);
        hackrf_close(device);
    }
    hackrf_exit();
    exit(code);
}

int main() {
    hackrf_device* device = NULL;
    FILE* log_file = NULL;

    // Step 1 — initialize library
    int result = hackrf_init();
    if (result != HACKRF_SUCCESS) {
        printf("Error: failed to initialize libhackrf: %s\n", hackrf_error_name(result));
        return 1;
    }

    // Step 2 — open device
    result = hackrf_open(&device);
    if (result != HACKRF_SUCCESS) {
        printf("Error: failed to open HackRF: %s\n", hackrf_error_name(result));
        hackrf_exit();
        return 1;
    }

    // Step 3 — configure hardware
    result = hackrf_set_sample_rate(device, SAMPLE_RATE);
    if (result != HACKRF_SUCCESS) {
        printf("Error: failed to set sample rate: %s\n", hackrf_error_name(result));
        cleanup_and_exit(device, log_file, 1);
    }

    result = hackrf_set_lna_gain(device, GAIN);
    if (result != HACKRF_SUCCESS) {
        printf("Error: failed to set LNA gain: %s\n", hackrf_error_name(result));
        cleanup_and_exit(device, log_file, 1);
    }

    result = hackrf_set_vga_gain(device, GAIN / 2);
    if (result != HACKRF_SUCCESS) {
        printf("Error: failed to set VGA gain: %s\n", hackrf_error_name(result));
        cleanup_and_exit(device, log_file, 1);
    }

    printf("HackRF opened successfully\n");
    printf("Scanning %.1f MHz to %.1f MHz...\n\n",
           FREQ_START/1000000.0, FREQ_END/1000000.0);

    // Step 4 — open log file
    log_file = fopen("/home/adam/SDR_Projects/P3_SIGINT_Scanner/sigint_scan.csv", "w");
    if (log_file == NULL) {
        printf("Error: could not open log file\n");
        cleanup_and_exit(device, log_file, 1);
    }
    fprintf(log_file, "Frequency (MHz),Power (dB),Timestamp\n");

    // Step 5 — sweep frequency range
    for (uint32_t freq = FREQ_START; freq <= FREQ_END; freq += FREQ_STEP) {
        // Reset buffer flag
        samples_ready = 0;
    

        // Tune to frequency
        result = hackrf_set_freq(device, freq);
        if (result != HACKRF_SUCCESS) {
            printf("Warning: failed to set frequency %.1f MHz: %s\n",
                   freq/1000000.0, hackrf_error_name(result));
            continue;  // skip this frequency, try next one
        }

        // Start receiving
        result = hackrf_start_rx(device, rx_callback, NULL);
        if (result != HACKRF_SUCCESS) {
            printf("Error: failed to start RX: %s\n", hackrf_error_name(result));
            break;
        }

        // Wait for callback to fill buffer with timeout
        int timeout = 0;
        while (samples_ready == 0) {
            usleep(1);
            timeout++;
            if (timeout > TIMEOUT_LIMIT) {
                printf("Warning: timeout at %.1f MHz\n", freq/1000000.0);
                break;
            }
        }

        // Stop receiving
        hackrf_stop_rx(device);

        // Only compute and log if we actually got samples
        if (samples_ready == 1) {
            double power_db = compute_power(sample_buffer, sizeof(sample_buffer));

            if (power_db >= POWER_THRESHOLD) {
                // Print result
                printf("  %.1f MHz  -->  %.2f dB\n", freq/1000000.0, power_db);

                // Log to CSV
                time_t now = time(NULL);
                char timestamp[26];
                strftime(timestamp, sizeof(timestamp),
                         "%Y-%m-%d %H:%M:%S", localtime(&now));
                fprintf(log_file, "%.1f,%.2f,%s\n",
                        freq/1000000.0, power_db, timestamp);
            }
        }
    }

    // Step 6 — clean up
    hackrf_stop_rx(device);  // safe to call even if not running
    fclose(log_file);
    hackrf_close(device);
    hackrf_exit();

    printf("\nResults saved to sigint_scan.csv\n");
    printf("Scan complete\n");
    return 0;
}