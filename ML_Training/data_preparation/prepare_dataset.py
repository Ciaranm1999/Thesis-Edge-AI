"""
prepare_dataset.py
==================
Cleans, validates, and exports the mould prediction sensor dataset for ESP32 deployment.

Pipeline:
  1. Load all_batches_ml_curated.csv
  2. Patch batch4 mould_start (confirmed post-collection, not in CSV)
  3. Derive binary mould label from mould_start timestamps
  4. Drop eCO2 columns (inaccurate on SGP30 in high-VOC environments)
  5. Drop all master node features (ambient air - negligible correlation with mould label)
  6. Mark saturated TVOC readings as NaN (SGP30 saturates at ~60,000 ppb)
  7. Drop rows with any null MQ3 (ethanol) readings
  8. Impute remaining TVOC NaN with per-batch median
  9. Compute delta TVOC (rate of change per batch) - first row of each batch = 0
  10. Apply train/test batch split
  11. Normalise features using TRAINING SET statistics only
  12. Export cleaned CSVs, JSON stats, and C header for ESP32

Train/test split rationale (Option B):
  Train : Batches 1, 2, 3, 4 (high-temp + low-temp, all with mould)
  Test  : Batch 5            (low-temp, unseen batch - temporal holdout)

  Including B4 in training means the model sees both temperature regimes.
  B5 is a genuinely unseen batch with different mould onset timing.

Features (10 total):
  node1_temp,        node1_hum,        node1_tvoc,        node1_mq3_ppm
  node2_temp,        node2_hum,        node2_tvoc,        node2_mq3_ppm
  delta_node1_tvoc,  delta_node2_tvoc

  Master node features excluded: ambient air shows negligible correlation with mould
  onset (Spearman |r| < 0.05 for master_tvoc, master_mq3_ppm, master_hum).

  delta_tvoc rationale: removes inter-batch TVOC baseline variance; captures the rate
  of VOC rise before sensor saturation; trivially computed on ESP32 (store one float
  between cycles). First row of each batch set to 0 (no prior reading).

Label:
  0 = pre-mould or no-mould period
  1 = mould detected (timestamp >= mould_start for that batch)
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT  = SCRIPT_DIR.parent.parent
DATA_DIR   = REPO_ROOT / "RaspberryPi" / "RaspberryPiData"
CSV_IN     = DATA_DIR / "analysis_exports" / "all_batches_ml_curated.csv"
OUT_DIR    = SCRIPT_DIR / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ESP32_DIR  = REPO_ROOT / "ML_Training" / "esp32_datasets"
ESP32_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TVOC_SATURATION = 59_000          # ppb - SGP30 max is 60,000; treat >=59k as saturated
BATCH4_MOULD_START = "2026-03-11 14:42:21"  # confirmed post-collection, not in CSV

ECO2_COLS    = ["master_eco2",    "node1_eco2",    "node2_eco2"]
MASTER_COLS  = ["master_temp",    "master_hum",    "master_tvoc", "master_mq3_ppm"]
NODE_TVOC_COLS = ["node1_tvoc",   "node2_tvoc"]
NODE_MQ3_COLS  = ["node1_mq3_ppm","node2_mq3_ppm"]
ALL_TVOC_COLS  = ["master_tvoc",  "node1_tvoc",    "node2_tvoc"]   # for saturation masking

# 10 features: 8 raw node features + 2 delta TVOC
RAW_FEATURE_COLS = [
    "node1_temp", "node1_hum", "node1_tvoc", "node1_mq3_ppm",
    "node2_temp", "node2_hum", "node2_tvoc", "node2_mq3_ppm",
]
DELTA_COLS   = ["delta_node1_tvoc", "delta_node2_tvoc"]
FEATURE_COLS = RAW_FEATURE_COLS + DELTA_COLS   # 10 features

TRAIN_BATCHES = ["Batch1", "batch2", "batch3", "batch4"]   # both regimes
TEST_BATCHES  = ["batch5"]                                 # unseen low-temp batch

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
print("=" * 60)
print("MOULD PREDICTION DATASET PREPARATION")
print("=" * 60)

if not CSV_IN.exists():
    sys.exit(f"ERROR: Could not find {CSV_IN}")

df = pd.read_csv(CSV_IN, parse_dates=["timestamp", "mould_start"])
print(f"\nLoaded: {len(df)} rows, {len(df.columns)} columns")
print(f"Batches: {df['batch'].unique().tolist()}")

# ---------------------------------------------------------------------------
# 2. Patch batch4 mould_start (confirmed post-collection - not in CSV)
# ---------------------------------------------------------------------------
df.loc[df["batch"] == "batch4", "mould_start"] = pd.Timestamp(BATCH4_MOULD_START)
print(f"\nPatched batch4 mould_start = {BATCH4_MOULD_START}")

# ---------------------------------------------------------------------------
# 3. Derive binary mould label
# ---------------------------------------------------------------------------
def derive_label(row):
    if pd.isna(row["mould_start"]):
        return 0
    return 1 if row["timestamp"] >= row["mould_start"] else 0

df["label"] = df.apply(derive_label, axis=1)
print(f"\nLabel distribution (raw):")
print(df["label"].value_counts().to_string())

# ---------------------------------------------------------------------------
# 4. Drop eCO2 columns
# ---------------------------------------------------------------------------
print(f"\nDropping eCO2 columns: {ECO2_COLS}")
print("  Reason: SGP30 eCO2 is estimated from TVOC, not measured. Unreliable.")
df.drop(columns=ECO2_COLS, inplace=True)

# ---------------------------------------------------------------------------
# 5. Drop master node features
# ---------------------------------------------------------------------------
print(f"\nDropping master node features: {MASTER_COLS}")
print("  Reason: master measures ambient room air, not the cargo microclimate.")
print("  Spearman |r| < 0.05 vs mould label for master_tvoc, master_mq3_ppm,")
print("  master_hum. master_temp is redundant with node temps (r=0.97).")
df.drop(columns=MASTER_COLS, inplace=True)

# ---------------------------------------------------------------------------
# 6. Mark saturated TVOC as NaN (node columns only; master already dropped)
# ---------------------------------------------------------------------------
sat_counts = {}
for col in NODE_TVOC_COLS:
    mask = df[col] >= TVOC_SATURATION
    sat_counts[col] = mask.sum()
    df.loc[mask, col] = np.nan

print(f"\nTVOC saturation (>= {TVOC_SATURATION:,} ppb) -- set to NaN:")
for col, n in sat_counts.items():
    pct = 100 * n / len(df)
    print(f"  {col}: {n} readings ({pct:.1f}%)")

print("\n  Per-batch saturation detail:")
for batch in df["batch"].unique():
    b = df[df["batch"] == batch]
    for col in NODE_TVOC_COLS:
        n = b[col].isna().sum()
        if n > 0:
            print(f"    {batch} / {col}: {n}/{len(b)} saturated")

# ---------------------------------------------------------------------------
# 7. Drop rows with null MQ3 readings
# ---------------------------------------------------------------------------
before = len(df)
df.dropna(subset=NODE_MQ3_COLS, inplace=True)
after = len(df)
print(f"\nDropped {before - after} rows with null MQ3 (ethanol) readings")
print(f"  Remaining: {after} rows")

# ---------------------------------------------------------------------------
# 8. Impute remaining TVOC NaN with per-batch median, falling back to
#    global training-set median when an entire batch is saturated (e.g.
#    batch2 node1_tvoc is 100% saturated — its per-batch median is NaN).
# ---------------------------------------------------------------------------
print("\nImputing remaining TVOC NaN:")
for col in NODE_TVOC_COLS:
    n_nan = df[col].isna().sum()
    if n_nan == 0:
        continue
    # Pass 1: per-batch median
    batch_medians = df.groupby("batch")[col].transform("median")
    df[col].fillna(batch_medians, inplace=True)
    n_remaining = df[col].isna().sum()
    if n_remaining > 0:
        # Pass 2: global median across all non-null values (handles fully-saturated batches)
        global_median = df[col].median()
        df[col].fillna(global_median, inplace=True)
        print(f"  {col}: {n_nan - n_remaining} batch-median imputed, "
              f"{n_remaining} global-median imputed (entire batch saturated, "
              f"global median = {global_median:.0f} ppb)")
    else:
        print(f"  {col}: {n_nan} values imputed with per-batch median")

# ---------------------------------------------------------------------------
# 9. Compute delta TVOC (rate of change within each batch)
#    First row of each batch = 0 (no prior reading available)
# ---------------------------------------------------------------------------
print("\nComputing delta TVOC (rate of change per reading, within each batch):")
for raw_col, delta_col in [("node1_tvoc", "delta_node1_tvoc"),
                            ("node2_tvoc", "delta_node2_tvoc")]:
    df[delta_col] = df.groupby("batch")[raw_col].diff().fillna(0.0)
    print(f"  {delta_col}: min={df[delta_col].min():.0f}  max={df[delta_col].max():.0f}  "
          f"mean={df[delta_col].mean():.0f}")

# Verify no NaN remains in features
remaining_nan = df[FEATURE_COLS].isna().sum().sum()
if remaining_nan > 0:
    print(f"\nWARNING: {remaining_nan} NaN values remain in features after imputation")
    print(df[FEATURE_COLS].isna().sum())
else:
    print("\nNo NaN values remain in feature columns.")

# ---------------------------------------------------------------------------
# 10. Train / Test split (Option B)
# ---------------------------------------------------------------------------
train_df = df[df["batch"].isin(TRAIN_BATCHES)].copy()
test_df  = df[df["batch"].isin(TEST_BATCHES)].copy()

print(f"\nData split:")
print(f"  Train (Batches 1,2,3,4 - both regimes, with mould): {len(train_df)} samples")
print(f"  Test  (Batch 5 - low temp, unseen):                 {len(test_df)} samples")

print(f"\nClass balance:")
for name, split in [("Train", train_df), ("Test", test_df)]:
    counts = split["label"].value_counts().sort_index()
    total  = len(split)
    mould_pct = 100 * counts.get(1, 0) / total
    print(f"  {name:<8}: {counts.get(0,0)} no-mould ({100-mould_pct:.0f}%) | "
          f"{counts.get(1,0)} mould ({mould_pct:.0f}%)")

# ---------------------------------------------------------------------------
# 11. Normalise features - fit on TRAINING set only
# ---------------------------------------------------------------------------
X_train = train_df[FEATURE_COLS].values.astype(np.float32)
X_test  = test_df[FEATURE_COLS].values.astype(np.float32)

y_train = train_df["label"].values.astype(np.uint8)
y_test  = test_df["label"].values.astype(np.uint8)

feat_min = X_train.min(axis=0)
feat_max = X_train.max(axis=0)
feat_range = feat_max - feat_min

# Avoid division by zero (constant feature)
feat_range[feat_range == 0] = 1.0

def normalise(X):
    return (X - feat_min) / feat_range

X_train_norm = normalise(X_train)
X_test_norm  = np.clip(normalise(X_test), 0.0, 1.0)  # clip in case test exceeds train range

print(f"\nNormalisation (min-max, fitted on training set):")
print(f"  {'Feature':<22} {'Min':>8} {'Max':>8} {'Range':>8}")
print(f"  {'-'*50}")
for i, col in enumerate(FEATURE_COLS):
    print(f"  {col:<22} {feat_min[i]:>8.3f} {feat_max[i]:>8.3f} {feat_range[i]:>8.3f}")

# ---------------------------------------------------------------------------
# 12. Export cleaned CSVs
# ---------------------------------------------------------------------------
def build_export_df(split_df, X_norm, y):
    out = split_df[["timestamp", "batch", "elapsed_hours"]].copy()
    for i, col in enumerate(FEATURE_COLS):
        out[col + "_norm"] = X_norm[:, i]
    out["label"] = y
    return out

build_export_df(train_df, X_train_norm, y_train).to_csv(OUT_DIR / "train.csv", index=False)
build_export_df(test_df,  X_test_norm,  y_test).to_csv(OUT_DIR  / "test.csv",  index=False)
print(f"\nCSVs saved to {OUT_DIR}")

# ---------------------------------------------------------------------------
# 13. Export dataset stats (for reference and manual normalisation on ESP32)
# ---------------------------------------------------------------------------
stats = {
    "feature_names": FEATURE_COLS,
    "n_features": len(FEATURE_COLS),
    "n_train": int(len(y_train)),
    "n_test":  int(len(y_test)),
    "train_batches": TRAIN_BATCHES,
    "test_batches":  TEST_BATCHES,
    "normalisation": "min-max fitted on training set",
    "feature_min":   feat_min.tolist(),
    "feature_max":   feat_max.tolist(),
    "feature_range": feat_range.tolist(),
    "train_class_balance": {
        "no_mould": int((y_train == 0).sum()),
        "mould":    int((y_train == 1).sum()),
    },
    "test_class_balance": {
        "no_mould": int((y_test == 0).sum()),
        "mould":    int((y_test == 1).sum()),
    },
    "exclusions": {
        "eco2": "Dropped - SGP30 eCO2 is TVOC-derived, unreliable in high-VOC environments",
        "master_features": "Dropped - ambient air; Spearman |r| < 0.05 vs mould label",
        "tvoc_saturation_threshold_ppb": TVOC_SATURATION,
        "mq3_null_rows": f"{before - after} rows dropped",
    },
    "engineered_features": {
        "delta_node1_tvoc": "TVOC rate of change per cycle within batch; first row = 0",
        "delta_node2_tvoc": "TVOC rate of change per cycle within batch; first row = 0",
    }
}

with open(OUT_DIR / "dataset_stats.json", "w") as f:
    json.dump(stats, f, indent=2)
print(f"Stats saved to {OUT_DIR / 'dataset_stats.json'}")

# ---------------------------------------------------------------------------
# 14. Export C header file for ESP32
# ---------------------------------------------------------------------------
def array_to_c(name, arr, dtype_c="float", indent=2):
    """Convert a numpy array to a C initialiser list string."""
    ind = " " * indent
    if arr.ndim == 1:
        vals = ", ".join(f"{v:.6f}f" if dtype_c == "float" else str(int(v))
                         for v in arr)
        return f"{{{vals}}}"
    else:
        rows = []
        for row in arr:
            vals = ", ".join(f"{v:.6f}f" if dtype_c == "float" else str(int(v))
                             for v in row)
            rows.append(f"{ind}{{{vals}}}")
        return "{\n" + ",\n".join(rows) + "\n}"

N_FEAT  = len(FEATURE_COLS)
N_TRAIN = len(y_train)
N_TEST  = len(y_test)

header_lines = [
    "/*",
    " * mould_prediction_dataset.h",
    " * Auto-generated by prepare_dataset.py",
    " *",
    " * Mould Prediction Dataset for ESP32",
    " * Features (10): node1_temp, node1_hum, node1_tvoc, node1_mq3_ppm,",
    " *                node2_temp, node2_hum, node2_tvoc, node2_mq3_ppm,",
    " *                delta_node1_tvoc, delta_node2_tvoc",
    " *",
    " * Master node features excluded (ambient air - negligible mould correlation).",
    " * delta_tvoc = TVOC[t] - TVOC[t-1] within each batch; first row = 0.",
    " *",
    " * Label: 0 = no mould, 1 = mould detected",
    " *",
    " * Normalisation: min-max, fitted on training set (Batches 1-4)",
    " * Apply before inference: x_norm = (x_raw - FEAT_MIN[i]) / FEAT_RANGE[i]",
    " * Clip result to [0.0, 1.0]",
    " *",
    f" * Train samples : {N_TRAIN} (Batches 1-4, both regimes, with mould)",
    f" * Test samples  : {N_TEST}  (Batch 5 - low-temp, unseen)",
    " */",
    "",
    "#pragma once",
    "#include <stdint.h>",
    "",
    f"#define N_FEATURES  {N_FEAT}",
    f"#define N_TRAIN     {N_TRAIN}",
    f"#define N_TEST      {N_TEST}",
    "",
    "/* --- Normalisation parameters ----------------------------------------- */",
    "",
    "static const float FEAT_MIN[N_FEATURES] = {",
]
header_lines.append("  " + ", ".join(f"{v:.6f}f" for v in feat_min))
header_lines += ["};", "", "static const float FEAT_MAX[N_FEATURES] = {"]
header_lines.append("  " + ", ".join(f"{v:.6f}f" for v in feat_max))
header_lines += ["};", "", "static const float FEAT_RANGE[N_FEATURES] = {"]
header_lines.append("  " + ", ".join(f"{v:.6f}f" for v in feat_range))
header_lines += ["};", ""]

# Feature name strings for debugging
header_lines += [
    "static const char* FEAT_NAMES[N_FEATURES] = {",
    "  " + ", ".join(f'"{n}"' for n in FEATURE_COLS),
    "};",
    "",
    "/* --- Training data ----------------------------------------------------- */",
    "",
    f"static const float train_X[N_TRAIN][N_FEATURES] = {array_to_c('train_X', X_train_norm)};",
    "",
    f"static const uint8_t train_y[N_TRAIN] = {{{', '.join(str(v) for v in y_train)}}};",
    "",
    "/* --- Test data --------------------------------------------------------- */",
    "",
    f"static const float test_X[N_TEST][N_FEATURES] = {array_to_c('test_X', X_test_norm)};",
    "",
    f"static const uint8_t test_y[N_TEST] = {{{', '.join(str(v) for v in y_test)}}};",
]

header_text = "\n".join(header_lines) + "\n"

header_path = ESP32_DIR / "mould_prediction_dataset.h"
with open(header_path, "w") as f:
    f.write(header_text)

print(f"C header saved to {header_path}")
header_kb = os.path.getsize(header_path) / 1024
print(f"  Header size: {header_kb:.1f} KB")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Features           : {N_FEAT}")
print(f"  Train samples : {N_TRAIN} "
      f"({int((y_train==0).sum())} no-mould / {int((y_train==1).sum())} mould)")
print(f"  Test samples  : {N_TEST} "
      f"({int((y_test==0).sum())} no-mould / {int((y_test==1).sum())} mould)")
print(f"\n  Outputs:")
print(f"    {OUT_DIR}/train.csv")
print(f"    {OUT_DIR}/test.csv")
print(f"    {OUT_DIR}/dataset_stats.json")
print(f"    {header_path}")
print("=" * 60)
