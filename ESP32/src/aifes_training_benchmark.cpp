/*
 * aifes_training_benchmark.cpp
 * ============================
 * AIfES full on-device training energy benchmark for ESP32 (Express API).
 * Option B v3 — per-epoch Fisher-Yates shuffle, 20 epochs, batch_size=4 (NaN fix).
 *
 * Three-part thesis comparison (infrastructure independence axis):
 *
 *   Step 1  AIfES / TFLM inference  94.0% / 93.7%
 *           Requires: PC training + cloud/USB deployment per update
 *           Real-world: large-scale operation with IT infrastructure
 *
 *   Step 2  TinyOL                  79.8% -> 86.1%
 *           Requires: one-time PC backbone pre-training, then no cloud
 *           Real-world: semi-professional setup, one training session
 *
 *   Step 3  AIfES full on-device    ? (this file)
 *           Requires: nothing — no PC, no internet, no pre-trained weights
 *           Real-world: fully autonomous node that learns entirely from its
 *                       own sensor readings accumulated over time
 *
 * Training data  : combined_training_dataset.h  (Batches 1+2+3+4, 1278 samples)
 *                  607 mould / 671 no-mould (approximately balanced)
 * Evaluation     : mould_prediction_dataset.h  (Batch 5, 332 samples, never seen)
 * Weight init    : Glorot uniform (AIfES_E_init_glorot_uniform, epoch 0 only)
 *
 * Optimizer   : Adam   LR=0.001
 * Loss        : CrossEntropy  (BCE)
 * Epochs      : 20
 * Batch size  : 4   (mini-batch — 20 x 320 = 6400 gradient steps)
 *
 * v3 change — NaN fix (batch_size 1 → 4):
 *   v2 (batch_size=1) produced a NaN loss on epoch 20. Root cause: with online
 *   Adam, the squared-gradient accumulator (v) can approach zero for parameters
 *   that receive near-zero gradients on consecutive samples. The Adam update
 *   θ -= lr * m / (√v + ε) then overflows when v ≈ 0. Increasing batch_size to 4
 *   averages 4 sample gradients before each parameter update, keeping v well away
 *   from zero. This is the standard fix for online-Adam numerical instability.
 *   Gradient clipping (the other standard fix) is not available in AIfES Express.
 *
 * Per-epoch shuffle — design note:
 *   AIfES_E_training_fnn_f32 runs the full epoch loop internally; there is no
 *   per-epoch callback to shuffle data. To achieve per-epoch shuffle we call the
 *   function once per epoch (epochs=1) with a freshly shuffled data copy.
 *
 *   LIMITATION: AIFES_E_training_fnn_f32 allocates Adam m/v accumulators on the
 *   heap at the start of each call and frees them at the end. Calling it once per
 *   epoch therefore RESETS the Adam momentum state between epochs — each epoch
 *   starts with zeroed m/v accumulators. This is a limitation of the AIfES Express
 *   API and is documented as a finding. The shuffle benefit is expected to outweigh
 *   the momentum-reset cost; the alternative (no shuffle, continuous Adam) produced
 *   69.3% in v1.
 *
 * PPK2 protocol: record energy between BENCHMARK START and BENCHMARK END.
 * Energy/update = total_energy_uJ / 25560
 *
 * Dependencies (platformio.ini env:aifes_training):
 *   https://github.com/Fraunhofer-IMS/AIfES_for_Arduino
 */

#include <Arduino.h>
#include <aifes.h>
#include <esp_random.h>    // hardware RNG for shuffle seed

#include "mould_prediction_dataset.h"      // test_X, test_y, N_TEST
#include "combined_training_dataset.h"     // combined_X, combined_y, N_COMBINED (1278)
#include "aifes_weights.h"                 // AIFES_INPUT_SIZE, AIFES_HIDDEN_SIZE, AIFES_OUTPUT_SIZE, AIFES_N_WEIGHTS

// ---------------------------------------------------------------------------
// Benchmark settings
// ---------------------------------------------------------------------------
#define EPOCHS      20
#define BATCH_SIZE  4       // mini-batch: fixes v2 NaN caused by online Adam v≈0
                            // 20 × ceil(1278/4) = 20 × 320 = 6400 gradient steps
#define LR          0.001f
#define THRESHOLD   0.45f
#define LED_PIN     2

// Each epoch: ceil(N_COMBINED / BATCH_SIZE) gradient steps
// 1278 / 4 = 319.5 → AIfES processes 320 batches (last batch has 2 samples)
#define STEPS_PER_EPOCH  ((N_COMBINED + BATCH_SIZE - 1) / BATCH_SIZE)  // 320
#define TOTAL_UPDATES    (EPOCHS * STEPS_PER_EPOCH)                     // 6400

// ---------------------------------------------------------------------------
// Loss print callback — AIfES requires a non-null function pointer
// ---------------------------------------------------------------------------
static void printLoss(float loss) {
    Serial.printf("  [loss] %.6f\n", loss);
}

// ---------------------------------------------------------------------------
// Mutable weight buffer — Glorot init writes here on epoch 0
// ---------------------------------------------------------------------------
static float train_weights[AIFES_N_WEIGHTS];

// ---------------------------------------------------------------------------
// AIfES Express model
// ---------------------------------------------------------------------------
static uint32_t           nn_structure[3]   = {AIFES_INPUT_SIZE, AIFES_HIDDEN_SIZE, AIFES_OUTPUT_SIZE};
static AIFES_E_activations nn_activations[2];
static AIFES_E_model_parameter_fnn_f32 nn;

// ---------------------------------------------------------------------------
// Per-epoch shuffle buffers (BSS — not heap)
//   shuf_idx[]     — Fisher-Yates index array  (1278 × 2 B =  2.5 KB)
//   shuffled_X[][] — contiguous writable copy of combined_X in shuffled order
//                    (1278 × 10 × 4 B = 49.9 KB, stored in BSS not heap)
//   shuffled_tgt[] — labels in shuffled order  (1278 × 4 B =  5.0 KB)
// ---------------------------------------------------------------------------
static uint16_t shuf_idx[N_COMBINED];
static float    shuffled_X[N_COMBINED][N_FEATURES];
static float    shuffled_tgt[N_COMBINED];

// ---------------------------------------------------------------------------
// AIfES training output buffer (one row per sample)
// ---------------------------------------------------------------------------
static float train_output_data[N_COMBINED];

// ---------------------------------------------------------------------------
// Fisher-Yates in-place shuffle of shuf_idx[] using ESP32 hardware RNG
// ---------------------------------------------------------------------------
static void shuffleIndices() {
    for (int i = N_COMBINED - 1; i > 0; i--) {
        uint16_t j = (uint16_t)(esp_random() % (uint32_t)(i + 1));
        uint16_t tmp  = shuf_idx[i];
        shuf_idx[i]   = shuf_idx[j];
        shuf_idx[j]   = tmp;
    }
}

// ---------------------------------------------------------------------------
// Evaluate model on Batch 5; returns accuracy %
// ---------------------------------------------------------------------------
static float evaluateOnTestSet() {
    uint32_t correct = 0;
    float    in_buf[AIFES_INPUT_SIZE];
    float    out_buf[AIFES_OUTPUT_SIZE];
    uint16_t in_shape[]  = {1, AIFES_INPUT_SIZE};
    uint16_t out_shape[] = {1, AIFES_OUTPUT_SIZE};

    for (int i = 0; i < N_TEST; i++) {
        memcpy(in_buf, test_X[i], AIFES_INPUT_SIZE * sizeof(float));
        aitensor_t in_t  = AITENSOR_2D_F32(in_shape,  in_buf);
        aitensor_t out_t = AITENSOR_2D_F32(out_shape, out_buf);
        AIFES_E_inference_fnn_f32(&in_t, &nn, &out_t);
        if ((out_buf[0] >= THRESHOLD ? 1 : 0) == (int)test_y[i]) correct++;
    }
    return 100.0f * (float)correct / (float)N_TEST;
}

// ---------------------------------------------------------------------------
// Setup — benchmark runs once; loop() does nothing
// ---------------------------------------------------------------------------
void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    Serial.begin(115200);
    while (!Serial) delay(10);

    Serial.println("\n========================================");
    Serial.println("  AIfES Full On-Device Training  [Step 3 — Option B v3]");
    Serial.println("  ZERO CLOUD: no PC weights, no internet, no pre-training");
    Serial.println("  Per-epoch Fisher-Yates shuffle (ESP32 HW RNG)");
    Serial.println("  Init: Glorot uniform (epoch 0) | Adam/BCE | 20 epochs, batch=4");
    Serial.println("  batch=4: fixes v2 NaN (online Adam v-accumulator underflow)");
    Serial.println("========================================");
    Serial.printf("  Total params      : %d floats  (all trainable)\n", AIFES_N_WEIGHTS);
    Serial.printf("  Training data     : Batches 1+2+3+4 (combined) — %d samples (%d mould / %d no-mould)\n",
                  N_COMBINED, N_COMBINED_POS, N_COMBINED_NEG);
    Serial.printf("  Evaluation data   : Batch 5 (test) — %d samples (never seen)\n", N_TEST);
    Serial.printf("  Epochs            : %d\n", EPOCHS);
    Serial.printf("  Batch size        : %d  (online, per-sample)\n", BATCH_SIZE);
    Serial.printf("  Learning rate     : %.5f  (Adam)\n", LR);
    Serial.printf("  Total updates     : %d  (%d epochs x %d batches of %d)\n",
                  TOTAL_UPDATES, EPOCHS, STEPS_PER_EPOCH, BATCH_SIZE);

    // -------------------------------------------------------------------
    // Build AIfES model (Glorot init happens on first training call)
    // -------------------------------------------------------------------
    nn_activations[0]  = AIfES_E_relu;
    nn_activations[1]  = AIfES_E_sigmoid;
    nn.layer_count     = 3;
    nn.fnn_structure   = nn_structure;
    nn.fnn_activations = nn_activations;
    nn.flat_weights    = train_weights;

    // Initialise index array 0..N_COMBINED-1
    for (int i = 0; i < N_COMBINED; i++) shuf_idx[i] = (uint16_t)i;

    // -------------------------------------------------------------------
    // Memory snapshot before benchmark
    // -------------------------------------------------------------------
    uint32_t heap_total  = ESP.getHeapSize();
    uint32_t heap_free_b = ESP.getFreeHeap();
    Serial.println("\n--- Memory (before benchmark) ---");
    Serial.printf("  Heap total         : %6u B  (%4.1f KB)\n", heap_total,  heap_total  / 1024.0f);
    Serial.printf("  Heap free          : %6u B  (%4.1f KB)\n", heap_free_b, heap_free_b / 1024.0f);
    Serial.printf("  Heap used          : %6u B  (%4.1f KB)\n",
                  heap_total - heap_free_b, (heap_total - heap_free_b) / 1024.0f);
    Serial.printf("  train_weights[]    : %6u B  (%4.1f KB)  [BSS]\n",
                  AIFES_N_WEIGHTS * 4, AIFES_N_WEIGHTS * 4 / 1024.0f);
    Serial.printf("  shuf_idx[]         : %6u B  (%4.1f KB)  [BSS]\n",
                  N_COMBINED * 2, N_COMBINED * 2 / 1024.0f);
    Serial.printf("  shuffled_X[][]     : %6u B  (%4.1f KB)  [BSS]\n",
                  N_COMBINED * N_FEATURES * 4, N_COMBINED * N_FEATURES * 4 / 1024.0f);
    Serial.printf("  shuffled_tgt[]     : %6u B  (%4.1f KB)  [BSS]\n",
                  N_COMBINED * 4, N_COMBINED * 4 / 1024.0f);
    Serial.printf("  combined_X[][]     : %6u B  (%4.1f KB)  [flash]\n",
                  N_COMBINED * N_FEATURES * 4, N_COMBINED * N_FEATURES * 4 / 1024.0f);
    Serial.printf("  AIfES heap/epoch   : ~%u B  (~%.1f KB)  [gradient + Adam m/v, freed each epoch]\n",
                  AIFES_N_WEIGHTS * 4 * 3, AIFES_N_WEIGHTS * 4 * 3 / 1024.0f);

    Serial.println("\nStarting in 2 seconds... (start PPK2 now)");
    delay(2000);

    // -------------------------------------------------------------------
    // Training config — epochs=1 per call; we loop externally for shuffle
    // -------------------------------------------------------------------
    AIFES_E_training_parameter_fnn_f32 train_cfg;
    train_cfg.loss                       = AIfES_E_crossentropy;
    train_cfg.optimizer                  = AIfES_E_adam;
    train_cfg.learn_rate                 = LR;
    train_cfg.sgd_momentum               = 0.0f;
    train_cfg.batch_size                 = BATCH_SIZE;
    train_cfg.epochs                     = 1;           // one epoch per call
    train_cfg.epochs_loss_print_interval = 1;           // print loss every epoch
    train_cfg.loss_print_function        = printLoss;
    train_cfg.early_stopping             = AIfES_E_early_stopping_off;
    train_cfg.early_stopping_target_loss = 0.0f;

    uint16_t in_shape[]  = {(uint16_t)N_COMBINED, (uint16_t)AIFES_INPUT_SIZE};
    uint16_t tgt_shape[] = {(uint16_t)N_COMBINED, (uint16_t)AIFES_OUTPUT_SIZE};
    uint16_t out_shape[] = {(uint16_t)N_COMBINED, (uint16_t)AIFES_OUTPUT_SIZE};

    // -------------------------------------------------------------------
    // BENCHMARK START — LED on, PPK2 recording
    // -------------------------------------------------------------------
    digitalWrite(LED_PIN, HIGH);
    Serial.println("=== BENCHMARK START ===");

    uint32_t t_start = micros();
    int8_t   last_err = 0;

    for (int epoch = 0; epoch < EPOCHS; epoch++) {
        // Shuffle index array (Fisher-Yates, ESP32 hardware RNG)
        shuffleIndices();

        // Build shuffled data copy in writable BSS buffer
        for (int i = 0; i < N_COMBINED; i++) {
            uint16_t src = shuf_idx[i];
            memcpy(shuffled_X[i], combined_X[src], N_FEATURES * sizeof(float));
            shuffled_tgt[i] = (float)combined_y[src];
        }

        aitensor_t in_t  = AITENSOR_2D_F32(in_shape,  shuffled_X);
        aitensor_t tgt_t = AITENSOR_2D_F32(tgt_shape, shuffled_tgt);
        aitensor_t out_t = AITENSOR_2D_F32(out_shape, train_output_data);

        AIFES_E_init_weights_parameter_fnn_f32 init_cfg;
        // Glorot init only on epoch 0; preserve weights for all subsequent epochs
        init_cfg.init_weights_method = (epoch == 0)
                                       ? AIfES_E_init_glorot_uniform
                                       : AIfES_E_init_no_init;

        Serial.printf("  Epoch %2d/%d ", epoch + 1, EPOCHS);
        last_err = AIFES_E_training_fnn_f32(&in_t, &tgt_t, &nn, &train_cfg, &init_cfg, &out_t);
        if (last_err != 0) {
            Serial.printf("ERROR %d — stopping\n", (int)last_err);
            break;
        }
    }

    uint32_t t_end = micros();
    // -------------------------------------------------------------------
    // BENCHMARK END
    // -------------------------------------------------------------------
    digitalWrite(LED_PIN, LOW);
    Serial.println("=== BENCHMARK END ===\n");

    if (last_err != 0) {
        Serial.println("Error codes: -5=crossentropy/softmax mismatch, -8=batch_size,");
        Serial.println("             -12=unknown optimizer, -13=out of memory");
        return;
    }

    // -------------------------------------------------------------------
    // Memory after benchmark
    // -------------------------------------------------------------------
    uint32_t heap_free_a = ESP.getFreeHeap();
    uint32_t min_free    = ESP.getMinFreeHeap();
    Serial.println("--- Memory (after benchmark) ---");
    Serial.printf("  Heap free after    : %6u B  (%4.1f KB)\n", heap_free_a, heap_free_a / 1024.0f);
    Serial.printf("  Min free (peak)    : %6u B  (%4.1f KB)\n", min_free,    min_free    / 1024.0f);
    Serial.printf("  Peak heap used     : %6u B  (%4.1f KB)\n",
                  heap_total - min_free, (heap_total - min_free) / 1024.0f);
    Serial.printf("  Heap leak          : %6d B  (0 expected)\n",
                  (int)heap_free_b - (int)heap_free_a);

    // -------------------------------------------------------------------
    // Accuracy AFTER training
    // -------------------------------------------------------------------
    float acc_after = evaluateOnTestSet();
    int   n_after   = (int)(acc_after * N_TEST / 100.0f + 0.5f);
    Serial.printf("\nAccuracy AFTER training  : %.1f%%  (%d / %d)\n",
                  acc_after, n_after, N_TEST);

    // -------------------------------------------------------------------
    // Timing results
    // -------------------------------------------------------------------
    uint32_t elapsed_us    = t_end - t_start;
    float    us_per_update = (float)elapsed_us / (float)TOTAL_UPDATES;

    Serial.println("\n--- Results ---");
    Serial.printf("  Total updates     : %d  (%d epochs x %d batches of %d)\n",
                  TOTAL_UPDATES, EPOCHS, STEPS_PER_EPOCH, BATCH_SIZE);
    Serial.printf("  Trainable params  : %d  (all: W1[%d]+B1[%d]+W2[%d]+B2[1])\n",
                  AIFES_N_WEIGHTS,
                  AIFES_INPUT_SIZE * AIFES_HIDDEN_SIZE,
                  AIFES_HIDDEN_SIZE,
                  AIFES_HIDDEN_SIZE * AIFES_OUTPUT_SIZE);
    Serial.printf("  Final accuracy    : %.1f%%\n", acc_after);
    Serial.printf("  Total time        : %u us (%.2f ms)\n", elapsed_us, elapsed_us / 1000.0f);
    Serial.printf("  Time/update       : %.1f us (%.3f ms)\n", us_per_update, us_per_update / 1000.0f);
    Serial.printf("  CPU cycles/update : ~%u cycles  (at 240 MHz)\n",
                  (uint32_t)(us_per_update * 240.0f));

    Serial.println("\nRecord PPK2 energy between BENCHMARK START and END.");
    Serial.printf("Energy/update = total_energy_uJ / %d  (each update = batch of %d samples)\n",
                  TOTAL_UPDATES, BATCH_SIZE);
    Serial.println("Step 3 Option B v3 — Zero cloud. Per-epoch shuffle. batch=4. No PC weights.");
}

void loop() {
    delay(10000);
}
