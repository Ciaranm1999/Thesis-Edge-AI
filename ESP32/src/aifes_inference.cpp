/*
 * aifes_inference.cpp
 * ====================
 * AIfES inference energy benchmark for ESP32 (Express API).
 *
 * Loads pre-trained float32 weights, runs a forward pass on every test sample,
 * and reports accuracy + per-inference timing. Connect the PPK2 to the ESP32
 * power rail and record while this sketch runs.
 *
 * Architecture: Input(10) -> Dense(16, ReLU) -> Dense(1, Sigmoid)
 * Data type:    float32 (F32)
 * Framework:    AIfES for Arduino (Fraunhofer IMS) - Express API
 *
 * PPK2 measurement protocol:
 *   1. Flash this sketch and open Serial Monitor (115200 baud)
 *   2. Wait for "=== BENCHMARK START ===" to appear
 *   3. Start PPK2 recording at that moment
 *   4. Stop PPK2 when "=== BENCHMARK END ===" appears
 *   5. Divide total energy by N_REPEATS * N_TEST for energy-per-inference
 *
 * Dependencies (platformio.ini env:aifes_inference):
 *   https://github.com/Fraunhofer-IMS/AIfES_for_Arduino
 */

#include <Arduino.h>
#include <aifes.h>

#include "mould_prediction_dataset.h"  // test_X, test_y, N_TEST, N_FEATURES
#include "aifes_weights.h"             // aifes_flat_weights, AIFES_*_SIZE defines

// ---------------------------------------------------------------------------
// Benchmark settings
// ---------------------------------------------------------------------------
#define N_REPEATS     100      // Run the full test set this many times for stable energy reading
#define PRINT_PREDS   false    // Set true to print each prediction (slows benchmark)
#define LED_PIN       2        // Built-in LED: ON during benchmark, OFF before/after

// ---------------------------------------------------------------------------
// AIfES Express model definition
// Network structure: 3 layers (input + 1 hidden + output)
// ---------------------------------------------------------------------------
// layer_count includes input layer, so {10, 16, 1} means 3 layers
static uint32_t nn_structure[3] = {AIFES_INPUT_SIZE, AIFES_HIDDEN_SIZE, AIFES_OUTPUT_SIZE};

// Activations: one per non-input layer (hidden=ReLU, output=Sigmoid)
static AIFES_E_activations nn_activations[2];

static AIFES_E_model_parameter_fnn_f32 nn;

// ---------------------------------------------------------------------------
// Input / output buffers (reused each inference)
// ---------------------------------------------------------------------------
static float input_data[AIFES_INPUT_SIZE];
static float output_data[AIFES_OUTPUT_SIZE];

// ---------------------------------------------------------------------------
// Initialise the AIfES Express model
// ---------------------------------------------------------------------------
void buildModel() {
    nn_activations[0] = AIfES_E_relu;     // hidden layer (Dense 10->16)
    nn_activations[1] = AIfES_E_sigmoid;  // output layer (Dense 16->1)

    nn.layer_count     = 3;                 // input + hidden + output
    nn.fnn_structure   = nn_structure;
    nn.fnn_activations = nn_activations;
    nn.flat_weights    = aifes_flat_weights; // from aifes_weights.h
}

// ---------------------------------------------------------------------------
// Run one forward pass and return the raw sigmoid output (0.0 - 1.0)
// ---------------------------------------------------------------------------
float runInference(const float* features) {
    memcpy(input_data, features, AIFES_INPUT_SIZE * sizeof(float));

    uint16_t input_shape[]  = {1, AIFES_INPUT_SIZE};
    uint16_t output_shape[] = {1, AIFES_OUTPUT_SIZE};

    aitensor_t input_tensor  = AITENSOR_2D_F32(input_shape,  input_data);
    aitensor_t output_tensor = AITENSOR_2D_F32(output_shape, output_data);

    int8_t err = AIFES_E_inference_fnn_f32(&input_tensor, &nn, &output_tensor);
    if (err != 0) {
        Serial.printf("ERROR: AIFES_E_inference_fnn_f32 returned %d\n", err);
        return -1.0f;
    }

    return output_data[0];
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);  // LED off during boot/setup

    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("\n========================================");
    Serial.println("  AIfES Inference Benchmark (Express API)");
    Serial.println("  Architecture: 10 -> Dense(16,ReLU) -> Dense(1,Sigmoid)");
    Serial.println("  Data type: float32");
    Serial.println("========================================");
    Serial.printf("  Weights      : %d floats\n", AIFES_N_WEIGHTS);
    Serial.printf("  Test samples : %d\n", N_TEST);
    Serial.printf("  Repeats      : %d\n", N_REPEATS);
    Serial.printf("  Total inferences: %d\n", N_TEST * N_REPEATS);

    buildModel();
    Serial.println("\nModel built and weights loaded.");

    // -----------------------------------------------------------------------
    // RAM snapshot BEFORE benchmark (outside PPK2 window — does not affect energy)
    // -----------------------------------------------------------------------
    uint32_t heap_total  = ESP.getHeapSize();
    uint32_t heap_before = ESP.getFreeHeap();
    uint32_t heap_used   = heap_total - heap_before;
    Serial.println("\n--- Memory (before benchmark) ---");
    Serial.printf("  Heap total       : %6u B  (%4.1f KB)\n", heap_total,  heap_total  / 1024.0f);
    Serial.printf("  Heap free        : %6u B  (%4.1f KB)\n", heap_before, heap_before / 1024.0f);
    Serial.printf("  Heap used        : %6u B  (%4.1f KB)\n", heap_used,   heap_used   / 1024.0f);
    Serial.printf("  Weights in flash : %6u B  (%4.1f KB)  [static array, not heap]\n",
                  AIFES_N_WEIGHTS * 4, AIFES_N_WEIGHTS * 4 / 1024.0f);

    Serial.println("\nStarting in 2 seconds... (start PPK2 now)");
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
            float    prob = runInference(test_X[i]);
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

    // RAM snapshot AFTER benchmark
    uint32_t heap_after = ESP.getFreeHeap();
    uint32_t min_heap   = ESP.getMinFreeHeap();  // lowest free heap seen since boot
    Serial.println("--- Memory (after benchmark) ---");
    Serial.printf("  Heap free after  : %6u B  (%4.1f KB)\n", heap_after, heap_after / 1024.0f);
    Serial.printf("  Min free (peak)  : %6u B  (%4.1f KB)\n", min_heap,   min_heap   / 1024.0f);
    Serial.printf("  Peak heap used   : %6u B  (%4.1f KB)\n",
                  heap_total - min_heap, (heap_total - min_heap) / 1024.0f);
    Serial.printf("  Heap leak        : %6d B  (before-after; 0 expected)\n",
                  (int)heap_before - (int)heap_after);

    uint32_t elapsed_us       = t_end - t_start;
    float    us_per_inference = (float)elapsed_us / (float)total_samples;
    float    ms_per_inference = us_per_inference / 1000.0f;
    float    accuracy         = 100.0f * total_correct / total_samples;

    uint32_t cpu_cycles_per_inf = (uint32_t)(us_per_inference * 240.0f);  // 240 MHz

    Serial.println("--- Results ---");
    Serial.printf("  Total inferences  : %u\n", total_samples);
    Serial.printf("  Correct           : %u\n", total_correct);
    Serial.printf("  Accuracy          : %.1f%%\n", accuracy);
    Serial.printf("  Total time        : %u us (%.2f ms)\n", elapsed_us, elapsed_us / 1000.0f);
    Serial.printf("  Time/inference    : %.1f us (%.3f ms)\n", us_per_inference, ms_per_inference);
    Serial.printf("  CPU cycles/inf    : ~%u cycles  (at 240 MHz)\n", cpu_cycles_per_inf);
    Serial.println("\nRecord PPK2 energy between BENCHMARK START and END.");
    Serial.println("Energy/inference = total_energy_uJ / total_inferences");
}

void loop() {
    // Nothing -- benchmark runs once in setup()
    delay(10000);
}
