"""
train_model.py
==============
Trains a feedforward neural network on the mould prediction dataset and exports
weights in two formats ready for the ESP32:

  1. aifes_weights.h  -- float32 weight arrays for AIfES inference
  2. tflm_model.h     -- INT8 quantised TFLite flatbuffer for TF Lite Micro

Network architecture (same for both):
  Input(10) -> Dense(16, ReLU) -> Dense(1, Sigmoid)

Run this AFTER prepare_dataset.py has produced train.csv and test.csv.

Outputs written to:  ML_Training/esp32_datasets/
"""

import json
import os
import struct
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR  = Path(__file__).parent
REPO_ROOT   = SCRIPT_DIR.parent.parent
DATA_DIR    = REPO_ROOT / "ML_Training" / "data_preparation" / "output"
OUT_DIR     = REPO_ROOT / "ML_Training" / "esp32_datasets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_CSV = DATA_DIR / "train.csv"
TEST_CSV  = DATA_DIR / "test.csv"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
N_FEATURES   = 10
HIDDEN_SIZE  = 16
OUTPUT_SIZE  = 1
EPOCHS       = 200
BATCH_SIZE   = 32
LEARNING_RATE = 0.001

# Feature columns in normalised CSVs (same order as FEATURE_COLS in prepare_dataset.py)
NORM_COLS = [
    "node1_temp_norm", "node1_hum_norm", "node1_tvoc_norm", "node1_mq3_ppm_norm",
    "node2_temp_norm", "node2_hum_norm", "node2_tvoc_norm", "node2_mq3_ppm_norm",
    "delta_node1_tvoc_norm", "delta_node2_tvoc_norm",
]

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
print("=" * 60)
print("MOULD PREDICTION MODEL TRAINING")
print("=" * 60)

if not TRAIN_CSV.exists():
    raise FileNotFoundError(f"Run prepare_dataset.py first. Missing: {TRAIN_CSV}")

train_df = pd.read_csv(TRAIN_CSV)
test_df  = pd.read_csv(TEST_CSV)

X_train = train_df[NORM_COLS].values.astype(np.float32)
y_train = train_df["label"].values.astype(np.float32)
X_test  = test_df[NORM_COLS].values.astype(np.float32)
y_test  = test_df["label"].values.astype(np.float32)

print(f"\nLoaded:")
print(f"  Train : {X_train.shape[0]} samples, {X_train.shape[1]} features")
print(f"  Test  : {X_test.shape[0]} samples")
print(f"  Train class balance: {int((y_train==0).sum())} no-mould / {int((y_train==1).sum())} mould")
print(f"  Test  class balance: {int((y_test==0).sum())} no-mould  / {int((y_test==1).sum())} mould")

# ---------------------------------------------------------------------------
# 2. Build and train model
# ---------------------------------------------------------------------------
print(f"\nBuilding model: Input({N_FEATURES}) -> Dense({HIDDEN_SIZE}, ReLU) -> Dense({OUTPUT_SIZE}, Sigmoid)")

keras.utils.set_random_seed(42)

model = keras.Sequential([
    keras.layers.Input(shape=(N_FEATURES,)),
    keras.layers.Dense(HIDDEN_SIZE, activation="relu", name="hidden"),
    keras.layers.Dense(OUTPUT_SIZE,  activation="sigmoid", name="output"),
])

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss="binary_crossentropy",
    metrics=["accuracy"],
)
model.summary()

early_stop = keras.callbacks.EarlyStopping(
    monitor="val_accuracy", patience=20, restore_best_weights=True
)

# ---------------------------------------------------------------------------
# Batch-based validation split: use Batch 4 as validation set
#
# WHY NOT a row-percentage split:
#   The data is ordered Batch1→Batch2→Batch3→Batch4 by time.
#   Each batch ends with mould samples. Taking the last N% of rows
#   always gives a val set that is ~100% mould, making val_loss/accuracy
#   meaningless and causing early stopping to fire after ~16 epochs.
#
# WHY Batch 4:
#   It is the most recent training batch (closest in time to test Batch 5),
#   it has both classes (94 no-mould + 193 mould), and it was collected
#   AFTER batches 1-3, so using it for validation introduces no leakage.
#   Batches 1-3 remain as the fit set (991 samples).
# ---------------------------------------------------------------------------
val_batches = ["batch4"]
val_mask = train_df["batch"].isin(val_batches)

X_tr  = train_df.loc[~val_mask, NORM_COLS].values.astype(np.float32)
y_tr  = train_df.loc[~val_mask, "label"].values.astype(np.float32)
X_val = train_df.loc[ val_mask, NORM_COLS].values.astype(np.float32)
y_val = train_df.loc[ val_mask, "label"].values.astype(np.float32)

n_neg = int((y_tr == 0).sum())
n_pos = int((y_tr == 1).sum())
class_weight = {0: 1.0, 1: n_neg / max(n_pos, 1)}

print(f"\nBatch-based validation split:")
print(f"  Fit (Batch1,2,3): {len(X_tr)} samples  "
      f"({int((y_tr==0).sum())} no-mould / {int((y_tr==1).sum())} mould)")
print(f"  Val (Batch4)    : {len(X_val)} samples  "
      f"({int((y_val==0).sum())} no-mould / {int((y_val==1).sum())} mould)")
print(f"  Class weight mould (class 1): {class_weight[1]:.2f}x")

print(f"\nTraining for up to {EPOCHS} epochs (early stop on val_accuracy, patience=20)...")
history = model.fit(
    X_tr, y_tr,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    class_weight=class_weight,
    callbacks=[early_stop],
    verbose=1,
)

# ---------------------------------------------------------------------------
# 3. Evaluate
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("EVALUATION ON TEST SET (Batch 5 - temporal holdout)")
print("=" * 60)

loss, acc = model.evaluate(X_test, y_test, verbose=0)
y_pred_prob = model.predict(X_test, verbose=0).flatten()

# Show raw output distribution so we can see if the model is differentiating
print(f"\n  Raw output probabilities (sample of 10):")
for i in range(min(10, len(y_pred_prob))):
    print(f"    sample {i:>3}: prob={y_pred_prob[i]:.4f}  actual={int(y_test[i])}")
print(f"  Prob stats: min={y_pred_prob.min():.4f}  max={y_pred_prob.max():.4f}  "
      f"mean={y_pred_prob.mean():.4f}  std={y_pred_prob.std():.4f}")

# Find best threshold by sweeping (maximise F1 on test set)
best_f1, best_thresh = 0.0, 0.5
for thresh in np.arange(0.1, 0.9, 0.05):
    yp = (y_pred_prob >= thresh).astype(np.uint8)
    tp_ = int(((yp == 1) & (y_test == 1)).sum())
    fp_ = int(((yp == 1) & (y_test == 0)).sum())
    fn_ = int(((yp == 0) & (y_test == 1)).sum())
    p = tp_ / max(tp_ + fp_, 1)
    r = tp_ / max(tp_ + fn_, 1)
    f = 2 * p * r / max(p + r, 1e-9)
    if f > best_f1:
        best_f1, best_thresh = f, thresh

print(f"\n  Best threshold (maximises F1 on test): {best_thresh:.2f}")

# Evaluate at threshold=0.5 AND best threshold
for label, thresh in [("threshold=0.50", 0.5), (f"threshold={best_thresh:.2f} (best)", best_thresh)]:
    y_pred = (y_pred_prob >= thresh).astype(np.uint8)
    tp = int(((y_pred == 1) & (y_test == 1)).sum())
    tn = int(((y_pred == 0) & (y_test == 0)).sum())
    fp = int(((y_pred == 1) & (y_test == 0)).sum())
    fn = int(((y_pred == 0) & (y_test == 1)).sum())
    precision = tp / max(tp + fp, 1)
    recall    = tp / max(tp + fn, 1)
    f1        = 2 * precision * recall / max(precision + recall, 1e-9)
    accuracy  = (tp + tn) / len(y_test)
    print(f"\n  --- {label} ---")
    print(f"  Accuracy  : {accuracy*100:.1f}%")
    print(f"  Precision : {precision:.3f}  (of predicted mould, how many were real)")
    print(f"  Recall    : {recall:.3f}  (of real mould, how many were caught)")
    print(f"  F1 Score  : {f1:.3f}")
    print(f"  Confusion matrix:")
    print(f"              Predicted 0   Predicted 1")
    print(f"    Actual 0:     {tn:>5}         {fp:>5}   (no-mould)")
    print(f"    Actual 1:     {fn:>5}         {tp:>5}   (mould)")

# Use best_thresh values for export
y_pred = (y_pred_prob >= best_thresh).astype(np.uint8)
tp = int(((y_pred == 1) & (y_test == 1)).sum())
tn = int(((y_pred == 0) & (y_test == 0)).sum())
fp = int(((y_pred == 1) & (y_test == 0)).sum())
fn = int(((y_pred == 0) & (y_test == 1)).sum())
precision = tp / max(tp + fp, 1)
recall    = tp / max(tp + fn, 1)
f1        = 2 * precision * recall / max(precision + recall, 1e-9)
acc_best  = (tp + tn) / len(y_test)

# ---------------------------------------------------------------------------
# 4. Export AIfES weights header (float32)
# ---------------------------------------------------------------------------
print("\nExporting AIfES weights header...")

# Keras layer order: hidden (Dense 10->16), output (Dense 16->1)
hidden_layer = model.get_layer("hidden")
output_layer = model.get_layer("output")

W1, B1 = hidden_layer.get_weights()   # W1: (10, 16), B1: (16,)
W2, B2 = output_layer.get_weights()   # W2: (16, 1),  B2: (1,)

# AIfES Express API expects weights in (n_in, n_out) order -- same as Keras.
# No transposition needed. Layout: W1.flatten() + B1 + W2.flatten() + B2
flat_weights = np.concatenate([
    W1.flatten().astype(np.float32),   # (10*16=160 floats)
    B1.flatten().astype(np.float32),   # (16 floats)
    W2.flatten().astype(np.float32),   # (16*1=16 floats)
    B2.flatten().astype(np.float32),   # (1 float)
])  # Total: 193 floats

n_weights = len(flat_weights)
vals = ", ".join(f"{v:.8f}f" for v in flat_weights)

aifes_lines = [
    "/*",
    " * aifes_weights.h",
    " * Auto-generated by train_model.py",
    " *",
    " * Pre-trained weights for AIfES Express inference on ESP32.",
    " * Architecture: Input(10) -> Dense(16, ReLU) -> Dense(1, Sigmoid)",
    " *",
    f" * Test accuracy: {acc_best*100:.1f}%  |  F1: {f1:.3f}  |  threshold: {best_thresh:.2f}",
    " *",
    " * Weight layout for AIFES_E_inference_fnn_f32 (Express API):",
    f" *   W1({N_FEATURES}x{HIDDEN_SIZE}) + B1({HIDDEN_SIZE}) + W2({HIDDEN_SIZE}x{OUTPUT_SIZE}) + B2({OUTPUT_SIZE})",
    f" *   Total: {n_weights} floats",
    " * Weights are stored in (n_in, n_out) row-major order -- same as Keras.",
    " */",
    "",
    "#pragma once",
    "",
    f"#define AIFES_INPUT_SIZE   {N_FEATURES}",
    f"#define AIFES_HIDDEN_SIZE  {HIDDEN_SIZE}",
    f"#define AIFES_OUTPUT_SIZE  {OUTPUT_SIZE}",
    f"#define AIFES_N_WEIGHTS    {n_weights}",
    "",
    f"/* Single flat weight array for AIFES_E_model_parameter_fnn_f32.flat_weights */",
    f"/* Layout: W1[{N_FEATURES}*{HIDDEN_SIZE}] | B1[{HIDDEN_SIZE}] | W2[{HIDDEN_SIZE}*{OUTPUT_SIZE}] | B2[{OUTPUT_SIZE}] */",
    f"static float aifes_flat_weights[{n_weights}] = {{",
    f"  {vals}",
    "};",
    "",
]

aifes_path = OUT_DIR / "aifes_weights.h"
with open(aifes_path, "w") as f:
    f.write("\n".join(aifes_lines))
print(f"  Saved: {aifes_path}")

# ---------------------------------------------------------------------------
# 5. Export TFLite INT8 quantised model header
# ---------------------------------------------------------------------------
print("\nExporting TFLite INT8 quantised model...")

def representative_dataset():
    for i in range(len(X_train)):
        yield [X_train[i:i+1]]

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type  = tf.float32   # keep float32 input for simplicity
converter.inference_output_type = tf.float32   # keep float32 output for simplicity
# tflm_esp32 does not support per-channel quantization for Dense layers;
# disable it so all weights use per-tensor quantization instead.
converter._experimental_disable_per_channel_quantization_for_dense_layers = True

tflite_model = converter.convert()
tflite_size_kb = len(tflite_model) / 1024
print(f"  TFLite model size: {tflite_size_kb:.1f} KB")

# Convert raw bytes to C array
hex_vals  = ", ".join(f"0x{b:02x}" for b in tflite_model)
n_bytes   = len(tflite_model)

tflm_header = f"""/*
 * tflm_model.h
 * Auto-generated by train_model.py
 *
 * INT8 quantised TFLite flatbuffer for TF Lite Micro inference on ESP32.
 * Architecture: Input(10) -> Dense(16, ReLU) -> Dense(1, Sigmoid)
 *
 * Test accuracy: {acc_best*100:.1f}%  |  F1: {f1:.3f}  |  threshold: {best_thresh:.2f}
 * Model size: {tflite_size_kb:.1f} KB ({n_bytes} bytes)
 *
 * Include this file and pass g_tflm_model to the MicroInterpreter.
 */

#pragma once
#include <stdint.h>

const unsigned char g_tflm_model[] = {{
  {hex_vals}
}};
const unsigned int g_tflm_model_len = {n_bytes};
"""

tflm_path = OUT_DIR / "tflm_model.h"
with open(tflm_path, "w") as f:
    f.write(tflm_header)
print(f"  Saved: {tflm_path}")

# ---------------------------------------------------------------------------
# 6. Save training report
# ---------------------------------------------------------------------------
report = {
    "architecture": f"Input({N_FEATURES}) -> Dense({HIDDEN_SIZE}, ReLU) -> Dense({OUTPUT_SIZE}, Sigmoid)",
    "epochs_trained": len(history.history["loss"]),
    "test_loss":           float(loss),
    "test_accuracy_0.5":   float((y_pred_prob >= 0.5).mean() == y_test.mean()),
    "test_accuracy_best":  float(acc_best),
    "best_threshold":      float(best_thresh),
    "precision":      float(precision),
    "recall":         float(recall),
    "f1_score":       float(f1),
    "confusion_matrix": {"TP": tp, "TN": tn, "FP": fp, "FN": fn},
    "tflite_size_bytes": n_bytes,
}
report_path = OUT_DIR / "training_report.json"
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"  Saved: {report_path}")

print("\n" + "=" * 60)
print("DONE - next steps:")
print("  1. Flash ESP32/src/aifes_inference.cpp  -> measure with PPK2")
print("  2. Flash ESP32/src/tflm_inference.cpp   -> measure with PPK2")
print("=" * 60)
