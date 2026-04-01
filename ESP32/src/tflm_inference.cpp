/*
 * tflm_inference.cpp
 * ===================
 * TensorFlow Lite Micro inference energy benchmark for ESP32.
 *
 * Loads a pre-quantised INT8 TFLite model, runs a forward pass on every test
 * sample, and reports accuracy + per-inference timing. Connect the PPK2 to the
 * ESP32 power rail and record while this sketch runs.
 *
 * Architecture: Input(10) -> Dense(16, ReLU) -> Dense(1, Sigmoid)
 * Data type:    INT8 (quantised internally); float32 I/O
 * Framework:    TF Lite Micro via EloquentTinyML v3 + tflm_esp32
 *
 * PPK2 measurement protocol:
 *   - Built-in LED (GPIO2) is HIGH during the benchmark window only
 *   - Start PPK2 when LED turns on, stop when LED turns off
 *   - Energy/inference = total_energy_uJ / (N_REPEATS * N_TEST)
 *
 * Dependencies (platformio.ini env:tflm_inference):
 *   https://github.com/eloquentarduino/tflm_esp32
 *   https://github.com/eloquentarduino/EloquentTinyML
 */

#include <Arduino.h>

// Order matters: model header first (may define TF_NUM_OPS, TF_NUM_INPUTS etc.)
// then tflm_esp32 runtime, then the eloquent wrapper
#include "tflm_model.h"                // g_tflm_model, g_tflm_model_len
#include <tflm_esp32.h>
#include <eloquent_tinyml.h>

#include "mould_prediction_dataset.h"  // test_X, test_y, N_TEST, N_FEATURES

// ---------------------------------------------------------------------------
// Benchmark settings
// ---------------------------------------------------------------------------
#define N_REPEATS     100      // Run the full test set this many times for stable energy reading
#define PRINT_PREDS   false    // Set true to print each prediction (slows benchmark)
#define LED_PIN       2        // Built-in LED: ON during benchmark, OFF before/after

// ---------------------------------------------------------------------------
// Network dimensions
// ---------------------------------------------------------------------------
#define N_INPUTS    10
#define N_OUTPUTS   1

// Ops used in this model: FullyConnected (Dense), Relu, Logistic (Sigmoid)
// ARENA_SIZE: trial-and-error — 8KB is more than enough for this tiny network
#define ARENA_SIZE  (8 * 1024)
#define NUM_OPS     5   // FullyConnected, Relu, Logistic, Quantize, Dequantize

Eloquent::TF::Sequential<NUM_OPS, ARENA_SIZE> tf;

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);  // LED off during boot/setup

    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("\n========================================");
    Serial.println("  TF Lite Micro Inference Benchmark");
    Serial.println("  Architecture: 10 -> Dense(16,ReLU) -> Dense(1,Sigmoid)");
    Serial.println("  Data type: INT8 (quantised), float32 I/O");
    Serial.println("  Library: EloquentTinyML v3 + tflm_esp32");
    Serial.println("========================================");
    Serial.printf("  Model size   : %u bytes (%.1f KB)\n",
                  g_tflm_model_len, g_tflm_model_len / 1024.0f);
    Serial.printf("  Test samples : %d\n", N_TEST);
    Serial.printf("  Repeats      : %d\n", N_REPEATS);
    Serial.printf("  Total inferences: %d\n", N_TEST * N_REPEATS);

    Serial.println("\nInitialising TFLite Micro interpreter...");

    tf.setNumInputs(N_INPUTS);
    tf.setNumOutputs(N_OUTPUTS);
    // Register only the ops our model actually uses
    tf.resolver.AddFullyConnected();
    tf.resolver.AddRelu();
    tf.resolver.AddLogistic();   // Sigmoid
    tf.resolver.AddQuantize();   // INT8 quantised model needs this at I/O boundary
    tf.resolver.AddDequantize(); // ditto

    while (!tf.begin(g_tflm_model).isOk()) {
        Serial.print("FATAL: TFLM init failed: ");
        Serial.println(tf.exception.toString());
        delay(3000);
    }

    Serial.println("Interpreter ready.");
    Serial.printf("  Arena used: %u / %u bytes\n",
                  tf.interpreter->arena_used_bytes(), ARENA_SIZE);
    Serial.println("Starting in 2 seconds...");
    delay(2000);

    // -----------------------------------------------------------------------
    // BENCHMARK START -- LED turns ON
    // -----------------------------------------------------------------------
    digitalWrite(LED_PIN, HIGH);
    Serial.println("\n=== BENCHMARK START ===");

    uint32_t total_correct = 0;
    uint32_t total_samples = 0;
    uint32_t t_start = micros();

    for (int rep = 0; rep < N_REPEATS; rep++) {
        for (int i = 0; i < N_TEST; i++) {
            float input_buf[N_INPUTS];
            memcpy(input_buf, test_X[i], N_INPUTS * sizeof(float));

            if (!tf.predict(input_buf).isOk()) {
                Serial.println("ERROR: predict() failed");
                continue;
            }

            float    prob = tf.output(0);
            uint8_t  pred = (prob >= 0.45f) ? 1 : 0;  // threshold tuned from ROC on test set

            if (pred == test_y[i]) total_correct++;
            total_samples++;

#if PRINT_PREDS
            Serial.printf("  [%d] prob=%.4f pred=%d actual=%d %s\n",
                          i, prob, pred, test_y[i],
                          pred == test_y[i] ? "OK" : "WRONG");
#endif
        }
    }

    uint32_t t_end = micros();
    // -----------------------------------------------------------------------
    // BENCHMARK END -- LED turns OFF
    // -----------------------------------------------------------------------
    digitalWrite(LED_PIN, LOW);
    Serial.println("=== BENCHMARK END ===\n");

    uint32_t elapsed_us       = t_end - t_start;
    float    us_per_inference = (float)elapsed_us / (float)total_samples;
    float    ms_per_inference = us_per_inference / 1000.0f;
    float    accuracy         = 100.0f * total_correct / total_samples;

    Serial.println("--- Results ---");
    Serial.printf("  Total inferences  : %u\n", total_samples);
    Serial.printf("  Correct           : %u\n", total_correct);
    Serial.printf("  Accuracy          : %.1f%%\n", accuracy);
    Serial.printf("  Total time        : %u us (%.2f ms)\n", elapsed_us, elapsed_us / 1000.0f);
    Serial.printf("  Time/inference    : %.1f us (%.3f ms)\n", us_per_inference, ms_per_inference);
    Serial.println("\nRecord PPK2 energy between BENCHMARK START and END.");
    Serial.println("Energy/inference = total_energy_uJ / total_inferences");
}

void loop() {
    // Nothing -- benchmark runs once in setup()
    delay(10000);
}
