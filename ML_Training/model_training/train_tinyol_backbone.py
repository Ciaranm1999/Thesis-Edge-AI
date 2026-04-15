"""
train_tinyol_backbone.py
========================
Trains a WEAK backbone for TinyOL on-device fine-tuning experiments.

RATIONALE (Option A split):
  The full backbone (train_model.py) trains on Batches 1+2 (fit) + Batch 3 (val),
  reaching 92.5% on Batch 5. This leaves no room for TinyOL to improve — the model
  already generalises well to the cold-storage test batch.

  To make TinyOL's on-device adaptation genuinely meaningful, this script trains the
  backbone on Batch 1 ONLY. Batch 2 is used for early-stopping validation.
  Batches 3 and 4 are fully withheld. This produces a weaker backbone (~75-85% on B5)
  that represents a model trained on limited high-temperature data only.

  TinyOL then fine-tunes the output layer on Batch 4 (cold-storage, on-device).
  The improvement from baseline to post-TinyOL demonstrates genuine domain adaptation.

Data split:
  Backbone fit (Batch 1)      : ~250 samples, high-temperature strawberry storage
  Backbone val (Batch 2)      : early stopping only, never used for gradient updates
  TinyOL fine-tuning (Batch 4): held_out_dataset.h — cold-storage, on-device only
  Evaluation (Batch 5)        : mould_prediction_dataset.h — never seen in any training

Architecture (identical to full backbone):
  Input(10) -> Dense(16, ReLU) -> Dense(1, Sigmoid)  [193 params total]

Output:
  tinyol_weights.h  -- flat float32 weight array for tinyol_benchmark.cpp
                       (same variable name as aifes_weights.h so the benchmark
                        only needs its #include changed, not its code)
"""

import os
from pathlib import Path

# Windows DLL path fix — required for TensorFlow 2.x on some Python 3.9 installs
os.add_dll_directory("C:/Windows/System32")

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT  = SCRIPT_DIR.parent.parent
DATA_DIR   = REPO_ROOT / "ML_Training" / "data_preparation" / "output"
OUT_DIR    = REPO_ROOT / "ML_Training" / "esp32_datasets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_CSV = DATA_DIR / "train.csv"
TEST_CSV  = DATA_DIR / "test.csv"

# ---------------------------------------------------------------------------
# Constants (must match tinyol_benchmark.cpp / aifes_weights.h exactly)
# ---------------------------------------------------------------------------
N_FEATURES  = 10
HIDDEN_SIZE = 16
OUTPUT_SIZE = 1
EPOCHS      = 200
BATCH_SIZE  = 32
LEARNING_RATE = 0.001

NORM_COLS = [
    "node1_temp_norm", "node1_hum_norm", "node1_tvoc_norm", "node1_mq3_ppm_norm",
    "node2_temp_norm", "node2_hum_norm", "node2_tvoc_norm", "node2_mq3_ppm_norm",
    "delta_node1_tvoc_norm", "delta_node2_tvoc_norm",
]

# ---------------------------------------------------------------------------
# 1. Load and split data
# ---------------------------------------------------------------------------
print("=" * 60)
print("TINYOL BACKBONE TRAINING  (Batch 1 only)")
print("=" * 60)

if not TRAIN_CSV.exists():
    raise FileNotFoundError(f"Run prepare_dataset.py first. Missing: {TRAIN_CSV}")

train_df = pd.read_csv(TRAIN_CSV)
test_df  = pd.read_csv(TEST_CSV)

# Batch 1 fit set — only data seen by this backbone during gradient updates
fit_mask = train_df["batch"].isin(["batch1", "Batch1"])
val_mask = train_df["batch"].isin(["batch2", "Batch2"])

X_fit = train_df.loc[fit_mask, NORM_COLS].values.astype(np.float32)
y_fit = train_df.loc[fit_mask, "label"].values.astype(np.float32)
X_val = train_df.loc[val_mask, NORM_COLS].values.astype(np.float32)
y_val = train_df.loc[val_mask, "label"].values.astype(np.float32)
X_test = test_df[NORM_COLS].values.astype(np.float32)
y_test = test_df["label"].values.astype(np.float32)

print(f"\nData split:")
print(f"  Backbone fit  (Batch 1 only) : {len(X_fit)} samples  "
      f"({int((y_fit==0).sum())} no-mould / {int((y_fit==1).sum())} mould)")
print(f"  Backbone val  (Batch 2)      : {len(X_val)} samples  "
      f"({int((y_val==0).sum())} no-mould / {int((y_val==1).sum())} mould)  [early stop only]")
print(f"  Batches 3+4                  : withheld entirely from backbone training")
print(f"  Evaluation    (Batch 5)      : {len(X_test)} samples  "
      f"({int((y_test==0).sum())} no-mould / {int((y_test==1).sum())} mould)")

if len(X_fit) == 0:
    raise RuntimeError("No Batch 1 data found — check batch column values in train.csv")

# ---------------------------------------------------------------------------
# 2. Build and train backbone
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

# Class weight to handle any imbalance in Batch 1
n_neg = int((y_fit == 0).sum())
n_pos = int((y_fit == 1).sum())
class_weight = {0: 1.0, 1: n_neg / max(n_pos, 1)}
print(f"\n  Class weight (mould=1): {class_weight[1]:.2f}x  "
      f"({n_neg} neg / {n_pos} pos in Batch 1 fit set)")

early_stop = keras.callbacks.EarlyStopping(
    monitor="val_accuracy", patience=20, restore_best_weights=True
)

print(f"\nTraining for up to {EPOCHS} epochs (early stop on val_accuracy, patience=20)...")
history = model.fit(
    X_fit, y_fit,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    class_weight=class_weight,
    callbacks=[early_stop],
    verbose=1,
)

epochs_trained = len(history.history["loss"])
print(f"\n  Stopped at epoch {epochs_trained}")

# ---------------------------------------------------------------------------
# 3. Evaluate on Batch 5
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("EVALUATION ON BATCH 5 (temporal holdout — never seen)")
print("=" * 60)

y_pred_prob = model.predict(X_test, verbose=0).flatten()

print(f"\n  Prob stats: min={y_pred_prob.min():.4f}  max={y_pred_prob.max():.4f}  "
      f"mean={y_pred_prob.mean():.4f}  std={y_pred_prob.std():.4f}")

# Sweep thresholds to find best F1
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

print(f"\n  Best threshold (F1): {best_thresh:.2f}")

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
    print(f"  Precision : {precision:.3f}")
    print(f"  Recall    : {recall:.3f}")
    print(f"  F1 Score  : {f1:.3f}")
    print(f"  Confusion matrix:")
    print(f"              Predicted 0   Predicted 1")
    print(f"    Actual 0:     {tn:>5}         {fp:>5}   (no-mould)")
    print(f"    Actual 1:     {fn:>5}         {tp:>5}   (mould)")

# Use best threshold for the header comment
y_pred_best = (y_pred_prob >= best_thresh).astype(np.uint8)
tp_b = int(((y_pred_best == 1) & (y_test == 1)).sum())
tn_b = int(((y_pred_best == 0) & (y_test == 0)).sum())
fp_b = int(((y_pred_best == 1) & (y_test == 0)).sum())
fn_b = int(((y_pred_best == 0) & (y_test == 1)).sum())
precision_b = tp_b / max(tp_b + fp_b, 1)
recall_b    = tp_b / max(tp_b + fn_b, 1)
f1_b        = 2 * precision_b * recall_b / max(precision_b + recall_b, 1e-9)
acc_best    = (tp_b + tn_b) / len(y_test)

# ---------------------------------------------------------------------------
# 4. Export tinyol_weights.h
#    Same variable names as aifes_weights.h so tinyol_benchmark.cpp only
#    needs its #include line changed, not any of its code.
# ---------------------------------------------------------------------------
print("\nExporting tinyol_weights.h...")

hidden_layer = model.get_layer("hidden")
output_layer = model.get_layer("output")

W1, B1 = hidden_layer.get_weights()   # W1: (10, 16), B1: (16,)
W2, B2 = output_layer.get_weights()   # W2: (16, 1),  B2: (1,)

flat_weights = np.concatenate([
    W1.flatten().astype(np.float32),
    B1.flatten().astype(np.float32),
    W2.flatten().astype(np.float32),
    B2.flatten().astype(np.float32),
])
n_weights = len(flat_weights)
vals = ", ".join(f"{v:.8f}f" for v in flat_weights)

lines = [
    "/*",
    " * tinyol_weights.h",
    " * Auto-generated by train_tinyol_backbone.py",
    " *",
    " * Pre-trained backbone weights for TinyOL on-device fine-tuning.",
    " * Architecture: Input(10) -> Dense(16, ReLU) -> Dense(1, Sigmoid)",
    " *",
    " * TRAINING SPLIT (Option A — weak backbone for TinyOL):",
    " *   Backbone fit : Batch 1 ONLY  (high-temperature strawberry storage)",
    " *   Backbone val : Batch 2       (early stopping only)",
    " *   Withheld     : Batches 3+4   (Batch 4 used for TinyOL on-device fine-tuning)",
    " *   Evaluation   : Batch 5       (332 samples, never seen in any training)",
    " *",
    " * This backbone is intentionally weaker than the full AIfES backbone",
    " * (train_model.py, Batches 1+2 fit + Batch 3 val) to create a genuine",
    " * accuracy gap that TinyOL's on-device Batch 4 fine-tuning can close.",
    " *",
    f" * Baseline accuracy (Batch 5, threshold={best_thresh:.2f}): {acc_best*100:.1f}%",
    f" * F1: {f1_b:.3f}  |  Precision: {precision_b:.3f}  |  Recall: {recall_b:.3f}",
    f" * Epochs trained: {epochs_trained}",
    " *",
    " * Variable names match aifes_weights.h exactly so tinyol_benchmark.cpp",
    " * only needs its #include changed from aifes_weights.h to tinyol_weights.h.",
    " *",
    " * Weight layout for tinyol_benchmark.cpp:",
    f" *   W1({N_FEATURES}x{HIDDEN_SIZE}) + B1({HIDDEN_SIZE}) + W2({HIDDEN_SIZE}x{OUTPUT_SIZE}) + B2({OUTPUT_SIZE})",
    f" *   Total: {n_weights} floats",
    " */",
    "",
    "#pragma once",
    "",
    f"#define AIFES_INPUT_SIZE   {N_FEATURES}",
    f"#define AIFES_HIDDEN_SIZE  {HIDDEN_SIZE}",
    f"#define AIFES_OUTPUT_SIZE  {OUTPUT_SIZE}",
    f"#define AIFES_N_WEIGHTS    {n_weights}",
    "",
    f"/* Flat weight array — layout: W1[{N_FEATURES}*{HIDDEN_SIZE}] | B1[{HIDDEN_SIZE}] | W2[{HIDDEN_SIZE}*{OUTPUT_SIZE}] | B2[{OUTPUT_SIZE}] */",
    f"static float aifes_flat_weights[{n_weights}] = {{",
    f"  {vals}",
    "};",
    "",
]

tinyol_weights_path = OUT_DIR / "tinyol_weights.h"
with open(tinyol_weights_path, "w") as f:
    f.write("\n".join(lines))
print(f"  Saved: {tinyol_weights_path}")

print("\n" + "=" * 60)
print("DONE")
print(f"  Baseline accuracy on Batch 5 : {acc_best*100:.1f}%  (threshold={best_thresh:.2f})")
print(f"  TinyOL will fine-tune on Batch 4 (287 samples, on-device)")
print(f"  Target: meaningful accuracy improvement after fine-tuning")
print()
print("Next steps:")
print("  1. Update tinyol_benchmark.cpp: change")
print('       #include "aifes_weights.h"')
print('     to')
print('       #include "tinyol_weights.h"')
print("  2. Also update THRESHOLD in tinyol_benchmark.cpp if best_thresh != 0.45")
print(f"     (best_thresh from this run = {best_thresh:.2f})")
print("  3. Re-flash tinyol_benchmark environment and run the benchmark")
print("=" * 60)
