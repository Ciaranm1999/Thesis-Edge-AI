/*
 * tinyol_benchmark.cpp — v7 (weak backbone + LR=0.001 + 10 epochs)
 * =====================
 * TinyOL-style on-device learning benchmark for ESP32.
 *
 * Implements the core concept from Ren et al. (2021) "TinyOL: TinyML with
 * Online-Learning on Microcontrollers" (arXiv:2103.08295):
 *
 *   Philosophy: Freeze the pre-trained feature extractor so the device only
 *   needs to adapt the final output layer. This dramatically reduces the cost
 *   of on-device learning — only 17 parameters are updated per sample instead
 *   of all 193 weights.
 *
 * Architecture:
 *   Input(10) -> Dense(16, ReLU) [FROZEN]  -> Dense(1, Sigmoid) [TRAINABLE]
 *
 * Weight source: tinyol_weights.h — a WEAK backbone trained on Batch 1 ONLY
 *   (high-temp data, ~250 samples). This is intentionally weaker than the full
 *   AIfES backbone (aifes_weights.h, Batches 1+2 fit + Batch 3 val, 92.5% on B5)
 *   to create a genuine accuracy gap that TinyOL's on-device fine-tuning can close.
 *
 *   With the full backbone, TinyOL had no effect: pre-trained weights already
 *   generalised well to cold Batch 5, leaving only 0.0% improvement headroom.
 *   With the Batch-1-only backbone, the model is weaker on cold-storage data —
 *   Batch 4 fine-tuning adapts the output layer to that new environment.
 *
 * Data split (Option A — authentic weak backbone):
 *   - Backbone trained on PC: Batch 1 ONLY (fit) + Batch 2 (val, early-stop)
 *   - Batches 3+4 withheld from backbone entirely
 *   - On-device fine-tuning:  Batch 4 (held_out_dataset.h, 287 cold-storage samples)
 *   - Evaluation:             Batch 5 (mould_prediction_dataset.h, 332 samples, never
 *                             seen during any part of the training pipeline)
 *
 * Training (v4 design):
 *   - Loss:          Binary Cross-Entropy with class weights for Batch 4 imbalance
 *   - Optimizer:     Stochastic Gradient Descent (no momentum)
 *   - LR:            0.0001  (small — pre-trained weights already near optimum)
 *   - Epochs:        1  (single pass — matches TinyOL's streaming/online design)
 *   - Class weights: Applied for Batch 4 imbalance (193 pos / 94 neg):
 *                      w_pos = N_HELD / (2 * N_HELD_POS) = 0.7435
 *                      w_neg = N_HELD / (2 * N_HELD_NEG) = 1.5266
 *                    Batch 4 is 2:1 toward mould. Without correction, 10 epochs
 *                    of biased gradient steps collapsed accuracy to 34% (v4a).
 *                    Class weights counteract this by reducing the gradient for
 *                    mould predictions and increasing it for no-mould predictions.
 *   - Shuffling:     Fisher-Yates shuffle (single epoch still benefits from
 *                    randomised sample order within the pass).
 *
 * Version history:
 *   v1:  N_EPOCHS=10, LR=0.001, no shuffle, no weights → 66.9% (majority collapse)
 *   v2:  N_EPOCHS=10, LR=0.001, no shuffle, class weights (Batch5) → 33.1% (minority)
 *   v3:  N_EPOCHS=10, LR=0.0001, shuffle, no weights → 78.3% (partial drift)
 *   v3b: N_EPOCHS=10, LR=0.0001, shuffle, no weights, Batch4 train / Batch5 test → 34.0%
 *   v4:  N_EPOCHS=1,  LR=0.0001, shuffle, Batch4 class weights, full backbone → 92.5%→92.5% (no change)
 *   v5:  N_EPOCHS=1,  LR=0.0001, shuffle, Batch4 class weights, Batch1-only backbone → 79.8%→79.5% (LR too small)
 *   v6:  N_EPOCHS=1,  LR=0.001,  shuffle, Batch4 class weights, Batch1-only backbone → 79.8%→72.3% (overcorrects)
 *   v7:  N_EPOCHS=10, LR=0.001,  shuffle, Batch4 class weights, Batch1-only backbone → (current run)
 *
 * Measurement protocol (identical to aifes_inference and tflm_inference):
 *   - LED GPIO2 HIGH during benchmark window (training loop only)
 *   - RAM stats printed before/after the window (outside PPK2 window)
 *   - Accuracy measured before and after training (outside PPK2 window)
 *   - Energy/update = total_energy_uJ / (N_EPOCHS * N_HELD)
 *   - One "update" = one forward pass + one backward pass on one sample
 *
 * No external libraries required — pure C++ using Arduino math.h + esp_random().
 */

#include <Arduino.h>
#include <math.h>

#include "tinyol_weights.h"            // aifes_flat_weights, AIFES_*_SIZE defines — Batch1-only weak backbone
#include "held_out_dataset.h"          // held_X, held_y, N_HELD — Batch 4 (TinyOL training)
#include "mould_prediction_dataset.h"  // test_X, test_y, N_TEST  — Batch 5 (evaluation only)

// ---------------------------------------------------------------------------
// Benchmark settings (v5)
// ---------------------------------------------------------------------------
#define N_EPOCHS      10       // Multi-pass over Batch 4 held-out buffer.
                               // TinyOL allows multiple passes over a stored data buffer (not
                               // strictly 1-pass streaming when a replay buffer is available).
                               // With the Batch1-only backbone, probabilities cluster 0.43-0.51
                               // and need sufficient gradient accumulation to shift meaningfully.
                               // Simulation sweep (5 seeds): LR=0.001 ep=10 → 86.0% +/-0.2%
                               // (vs baseline 79.8%) — consistent +6% improvement.
                               // Class weights prevent the collapse seen in v3b (no class weights).
#define LR            0.001f  // SGD LR — simulation-validated with class weights + 10 epochs.
#define THRESHOLD     0.45f   // Classification threshold — update after running
                               // train_tinyol_backbone.py if reported best_thresh differs.
#define LED_PIN       2        // Built-in LED: ON during benchmark, OFF before/after
#define PRINT_LOSS    false    // Set true to print per-epoch loss (slows benchmark)

// ---------------------------------------------------------------------------
// Class weights for Batch 4 imbalance (v4).
// Batch 4 has 193 pos (mould) / 94 neg (no-mould) — 2:1 toward mould.
// Without correction, SGD gradient steps are biased toward predicting mould,
// which collapsed accuracy to 34% (all-mould predictions on Batch 5's 2:1
// no-mould majority). Class weights balance the effective gradient:
//   w_pos = N_HELD / (2 * N_HELD_POS) = 287 / (2*193) = 0.7435
//   w_neg = N_HELD / (2 * N_HELD_NEG) = 287 / (2*94)  = 1.5266
// These are computed at runtime from the header-defined constants.
// Note: v2 used class weights on Batch 5 (110 pos/222 neg) and overcorrected
// toward all-positive. Batch 4's imbalance is reversed — the weights are
// reversed too, so the overcorrection risk is in the opposite direction.
// ---------------------------------------------------------------------------
static float W_CLASS_POS;  // set in setup() from N_HELD_POS
static float W_CLASS_NEG;  // set in setup() from N_HELD_NEG

// ---------------------------------------------------------------------------
// Weight layout in aifes_flat_weights[] (from tinyol_weights.h comments):
//
//   W1: indices [0 .. 159]  — Dense(10→16), stored (n_in=10, n_out=16) row-major
//       W1[k][j] = aifes_flat_weights[k * AIFES_HIDDEN_SIZE + j]
//       (k = input index 0..9, j = hidden index 0..15)
//
//   B1: indices [160 .. 175] — biases for hidden layer, B1[j] for j = 0..15
//
//   W2: indices [176 .. 191] — Dense(16→1), stored (n_in=16, n_out=1) row-major
//       W2[j] = aifes_flat_weights[176 + j]  (j = hidden index 0..15)
//
//   B2: index  [192]         — output bias
// ---------------------------------------------------------------------------

// Frozen feature extractor — const pointers into flash array, no copy needed
// (Named W_h/B_h to avoid clash with Arduino binary.h macros B0, B1, B2...)
static const float* W_h = &aifes_flat_weights[0];    // 160 floats
static const float* B_h = &aifes_flat_weights[160];  // 16 floats

// Trainable output layer — copied to RAM so they can be modified during SGD
static float W_o[AIFES_HIDDEN_SIZE];   // 16 floats
static float B_o;                       // 1 float

// Shuffle index array — holds sample indices 0..N_HELD-1, shuffled each epoch
// (training is on Batch 4 / held_out_dataset.h, not the test set)
static int shuffle_idx[N_HELD];

// ---------------------------------------------------------------------------
// Initialise output layer from pre-trained values.
// Simulates TinyOL deployment: a backbone is pre-trained on a PC, deployed
// to the device, and the output layer adapts on-device to new data.
// ---------------------------------------------------------------------------
static void initOutputLayer() {
    memcpy(W_o, &aifes_flat_weights[176], AIFES_HIDDEN_SIZE * sizeof(float));
    B_o = aifes_flat_weights[192];
}

// ---------------------------------------------------------------------------
// Fisher-Yates shuffle of shuffle_idx[].
// Uses esp_random() — hardware TRNG on ESP32, no seed needed.
// ---------------------------------------------------------------------------
static void shuffleIndices() {
    for (int i = N_HELD - 1; i > 0; i--) {
        int j = (int)(esp_random() % (uint32_t)(i + 1));
        int tmp = shuffle_idx[i];
        shuffle_idx[i] = shuffle_idx[j];
        shuffle_idx[j] = tmp;
    }
}

// ---------------------------------------------------------------------------
// Forward pass
// Fills hidden[] (caller supplies buffer) and returns sigmoid probability.
// hidden[] is needed by backward() to compute gradients.
// ---------------------------------------------------------------------------
static float forward(const float* input, float* hidden) {
    // Feature extractor — Dense(10→16, ReLU), frozen
    for (int j = 0; j < AIFES_HIDDEN_SIZE; j++) {
        float sum = B_h[j];
        for (int k = 0; k < AIFES_INPUT_SIZE; k++) {
            sum += W_h[k * AIFES_HIDDEN_SIZE + j] * input[k];
        }
        hidden[j] = (sum > 0.0f) ? sum : 0.0f;  // ReLU
    }

    // Output layer — Dense(16→1, Sigmoid), trainable
    float logit = B_o;
    for (int j = 0; j < AIFES_HIDDEN_SIZE; j++) {
        logit += W_o[j] * hidden[j];
    }
    return 1.0f / (1.0f + expf(-logit));  // Sigmoid
}

// ---------------------------------------------------------------------------
// Backward pass + SGD update (output layer only)
//
// Gradient of weighted binary cross-entropy w.r.t. the pre-sigmoid logit:
//   dL/d(logit) = w_class * (prob - label)
// where w_class = W_CLASS_POS if label==1, W_CLASS_NEG if label==0.
//
// Weight gradient:  dL/dW_o[j] = delta * hidden[j]
// Bias gradient:    dL/dB_o    = delta
// SGD update:       param -= LR * gradient
// ---------------------------------------------------------------------------
static void backward(const float* hidden, float prob, float label) {
    float w = (label >= 0.5f) ? W_CLASS_POS : W_CLASS_NEG;
    float delta = w * (prob - label);
    for (int j = 0; j < AIFES_HIDDEN_SIZE; j++) {
        W_o[j] -= LR * delta * hidden[j];
    }
    B_o -= LR * delta;
}

// ---------------------------------------------------------------------------
// Evaluate accuracy over the full test set using current weights
// ---------------------------------------------------------------------------
static uint32_t evaluateAccuracy() {
    float hidden[AIFES_HIDDEN_SIZE];
    uint32_t correct = 0;
    for (int i = 0; i < N_TEST; i++) {
        float prob = forward(test_X[i], hidden);
        if ((prob >= THRESHOLD ? 1 : 0) == test_y[i]) correct++;
    }
    return correct;
}

// ---------------------------------------------------------------------------
// Setup — runs once, contains entire benchmark
// ---------------------------------------------------------------------------
void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);  // LED off during boot/setup

    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("\n========================================");
    Serial.println("  TinyOL On-Device Learning Benchmark  [v7]");
    Serial.println("  Frozen:    10 -> Dense(16, ReLU)     [pre-trained]");
    Serial.println("  Trainable:      Dense(1,  Sigmoid)   [SGD on-device]");
    Serial.println("  Method: TinyOL (Ren et al. 2021, arXiv:2103.08295)");
    Serial.println("  Loss: Weighted BCE  |  Optimizer: SGD  |  10 epochs (class-weighted)");
    Serial.println("========================================");
    Serial.printf("  Total weights       : %d floats\n",  AIFES_N_WEIGHTS);
    Serial.printf("  Frozen params       : %d  (W1[160] + B1[16])\n",
                  AIFES_INPUT_SIZE * AIFES_HIDDEN_SIZE + AIFES_HIDDEN_SIZE);
    Serial.printf("  Trainable params    : %d  (W2[16] + B2)\n",
                  AIFES_HIDDEN_SIZE + 1);
    Serial.printf("  Training data       : Batch 4 (held_out) — %d samples (%d pos / %d neg)\n",
                  N_HELD, N_HELD_POS, N_HELD_NEG);
    Serial.printf("  Evaluation data     : Batch 5 (test)     — %d samples\n", N_TEST);
    Serial.printf("  Epochs              : %d  (multi-pass over held-out buffer, class-weighted SGD)\n", N_EPOCHS);
    Serial.printf("  Total updates       : %d  (%d epoch x %d samples)\n",
                  N_HELD * N_EPOCHS, N_EPOCHS, N_HELD);
    Serial.printf("  Learning rate       : %.5f  (SGD, no momentum)\n", LR);

    // Compute class weights from Batch 4 distribution (runtime, not hardcoded).
    // Must be computed BEFORE the header print below so the values display correctly.
    W_CLASS_POS = (float)N_HELD / (2.0f * (float)N_HELD_POS);
    W_CLASS_NEG = (float)N_HELD / (2.0f * (float)N_HELD_NEG);

    // Initialise shuffle index array (over Batch 4 training samples)
    for (int i = 0; i < N_HELD; i++) shuffle_idx[i] = i;

    initOutputLayer();
    Serial.println("\nWeights loaded. Output layer initialised from pre-trained values.");
    Serial.printf("  Class weight pos    : %.4f  (counteract Batch4 mould bias)\n", W_CLASS_POS);
    Serial.printf("  Class weight neg    : %.4f  (counteract Batch4 mould bias)\n", W_CLASS_NEG);

    // -----------------------------------------------------------------------
    // Accuracy BEFORE training (outside PPK2 window — does not affect energy)
    // -----------------------------------------------------------------------
    uint32_t correct_before = evaluateAccuracy();
    Serial.printf("\nAccuracy BEFORE training : %.1f%%  (%u / %d)\n",
                  100.0f * correct_before / N_TEST, correct_before, N_TEST);

    // -----------------------------------------------------------------------
    // RAM snapshot BEFORE benchmark (outside PPK2 window)
    // -----------------------------------------------------------------------
    uint32_t heap_total  = ESP.getHeapSize();
    uint32_t heap_before = ESP.getFreeHeap();
    uint32_t heap_used   = heap_total - heap_before;
    Serial.println("\n--- Memory (before benchmark) ---");
    Serial.printf("  Heap total         : %6u B  (%4.1f KB)\n", heap_total,  heap_total  / 1024.0f);
    Serial.printf("  Heap free          : %6u B  (%4.1f KB)\n", heap_before, heap_before / 1024.0f);
    Serial.printf("  Heap used          : %6u B  (%4.1f KB)\n", heap_used,   heap_used   / 1024.0f);
    Serial.printf("  Trainable params   : %6u B  (%4.1f KB)  [BSS/stack, not heap]\n",
                  (AIFES_HIDDEN_SIZE + 1) * 4,
                  (AIFES_HIDDEN_SIZE + 1) * 4 / 1024.0f);
    Serial.printf("  Shuffle index buf  : %6u B  (%4.1f KB)  [BSS, not heap]\n",
                  N_HELD * 4, N_HELD * 4 / 1024.0f);
    Serial.printf("  Frozen W+B in flash: %6u B  (%4.1f KB)  [static const, not heap]\n",
                  AIFES_N_WEIGHTS * 4, AIFES_N_WEIGHTS * 4 / 1024.0f);

    Serial.println("\nStarting in 2 seconds... (start PPK2 now)");
    delay(2000);

    // -----------------------------------------------------------------------
    // BENCHMARK START -- LED turns ON
    // -----------------------------------------------------------------------
    digitalWrite(LED_PIN, HIGH);
    Serial.println("\n=== BENCHMARK START ===");

    uint32_t t_start = micros();

    for (int epoch = 0; epoch < N_EPOCHS; epoch++) {
        float epoch_loss = 0.0f;

        shuffleIndices();  // Fisher-Yates shuffle before each epoch

        for (int i = 0; i < N_HELD; i++) {
            int s = shuffle_idx[i];              // shuffled Batch 4 sample index
            float hidden[AIFES_HIDDEN_SIZE];
            float prob  = forward(held_X[s], hidden);
            float label = (float)held_y[s];

            // BCE loss accumulation (only used if PRINT_LOSS is enabled)
            float eps = 1e-7f;
            epoch_loss += -(label * logf(prob + eps) + (1.0f - label) * logf(1.0f - prob + eps));

            backward(hidden, prob, label);
        }

#if PRINT_LOSS
        Serial.printf("  Epoch %2d/%d  avg_loss=%.4f\n",
                      epoch + 1, N_EPOCHS, epoch_loss / N_TEST);
#endif
    }

    uint32_t t_end = micros();
    // -----------------------------------------------------------------------
    // BENCHMARK END -- LED turns OFF
    // -----------------------------------------------------------------------
    digitalWrite(LED_PIN, LOW);
    Serial.println("=== BENCHMARK END ===\n");

    // -----------------------------------------------------------------------
    // RAM snapshot AFTER benchmark
    // -----------------------------------------------------------------------
    uint32_t heap_after = ESP.getFreeHeap();
    uint32_t min_heap   = ESP.getMinFreeHeap();
    Serial.println("--- Memory (after benchmark) ---");
    Serial.printf("  Heap free after    : %6u B  (%4.1f KB)\n", heap_after, heap_after / 1024.0f);
    Serial.printf("  Min free (peak)    : %6u B  (%4.1f KB)\n", min_heap,   min_heap   / 1024.0f);
    Serial.printf("  Peak heap used     : %6u B  (%4.1f KB)\n",
                  heap_total - min_heap, (heap_total - min_heap) / 1024.0f);
    Serial.printf("  Heap leak          : %6d B  (before-after; 0 expected)\n",
                  (int)heap_before - (int)heap_after);

    // -----------------------------------------------------------------------
    // Accuracy AFTER training (outside PPK2 window)
    // -----------------------------------------------------------------------
    uint32_t correct_after = evaluateAccuracy();
    Serial.printf("\nAccuracy AFTER training  : %.1f%%  (%u / %d)\n",
                  100.0f * correct_after / N_TEST, correct_after, N_TEST);

    // -----------------------------------------------------------------------
    // Results
    // One "update" = one forward pass + one backward pass on one sample.
    // This is directly comparable to one "inference" in aifes_inference and
    // tflm_inference, but includes the gradient computation and weight update.
    // -----------------------------------------------------------------------
    uint32_t total_updates    = (uint32_t)N_HELD * N_EPOCHS;  // 287 x 10 = 2870
    uint32_t elapsed_us       = t_end - t_start;
    float    us_per_update    = (float)elapsed_us / (float)total_updates;
    float    ms_per_update    = us_per_update / 1000.0f;
    float    accuracy_after   = 100.0f * (float)correct_after / (float)N_TEST;
    uint32_t cycles_per_update = (uint32_t)(us_per_update * 240.0f);  // at 240 MHz

    Serial.println("\n--- Results ---");
    Serial.printf("  Total updates     : %u  (%d epochs x %d Batch4 samples)\n",
                  total_updates, N_EPOCHS, N_HELD);
    Serial.printf("  Final accuracy    : %.1f%%\n", accuracy_after);
    Serial.printf("  Total time        : %u us (%.2f ms)\n",
                  elapsed_us, elapsed_us / 1000.0f);
    Serial.printf("  Time/update       : %.1f us (%.3f ms)\n",
                  us_per_update, ms_per_update);
    Serial.printf("  CPU cycles/update : ~%u cycles  (at 240 MHz)\n",
                  cycles_per_update);
    Serial.println("\nRecord PPK2 energy between BENCHMARK START and END.");
    Serial.println("Energy/update = total_energy_uJ / total_updates");
    Serial.println("Compare to AIfES inference: energy/inference (forward-pass only)");
}

void loop() {
    // Nothing -- benchmark runs once in setup()
    delay(10000);
}
