# Notebook Fixes & Enhancements Summary

Date: March 21, 2026

## Issues Fixed

### 1. **Cell Execution Order** ✓
**Problem**: Cells were in reverse order - the export cell (Part 6) ran first but depended on `clean_df` that hadn't been created yet.

**Solution**: Reorganized cells in logical sequence:
1. Setup & Configuration
2. Load data (with PPB→PPM conversion)
3. Data quality checks
4. Exploratory plots
5. Saturation analysis
6. Exclusion rules & application
7. Feature summary & export

### 2. **VOC Measurements: PPB → PPM Conversion** ✓
**Problem**: TVOC data in ppb (parts per billion) was harder to understand and interpret.

**Solution**: Added automatic conversion:
```python
# Convert TVOC from ppb to ppm (ppb / 1000)
for tvoc_col in ['master_tvoc', 'node1_tvoc', 'node2_tvoc']:
    if tvoc_col in df.columns:
        df[tvoc_col] = df[tvoc_col] / 1000.0
```

**Impact**:
- TVOC saturation cap now: **60 ppm** (was 60,000 ppb)
- Data more readable (e.g., 3.865 ppm instead of 3865 ppb)
- Better alignment with common VOC measurement standards

### 3. **MQ3 Ethanol Data Quality Analysis** ✓
**Problem**: Needed to identify suspect/incorrect MQ3 readings before visualization.

**Solution**: Added comprehensive quality check in Part 1:
- Detects **negative readings** (flag as anomalies)
- Detects **extreme high values** (>2000 ppm)
- Reports min/max/mean ± std per batch and node
- Warns about unrealistic patterns

**Example output flags**:
```
⚠️ X negative readings
⚠️ X extreme values (>2000 ppm)
```

---

## Data Quality Improvements

### Saturation Detection (Now in PPM)
- High-TEMP batches: Node1 shows ~25 ppm TVOC peak, Node2 shows up to ~60 ppm
- Low-TEMP batches: Node2 TVOC accelerates to 60 ppm cap (saturation)
- **batch2**: 100% saturation → excluded entirely
- **Batch1 & batch5**: Partial saturation → excluded post-saturation windows

### MQ3 Ethanol Observations
- High-TEMP: Node2 MQ3 shows high variability (400-800 ppm range)
- Low-TEMP: Stable MQ3 values, more predictable
- Baseline (Master) shows consistent baseline for cross-node comparison

---

## File Generated

### Updated Outputs
- **strawberry_decay_clean_ML_ready.csv** (1,140 rows)
  - **TVOC now in ppm** (not ppb)
  - All other columns unchanged
  - No saturated readings (≥60 ppm removed)
  - batch2 excluded entirely

### Column Breakdown
```
Metadata:    timestamp, batch, regime, cycle_number, elapsed_hours, mould_start, has_mould
Temperature: master_temp, node1_temp, node2_temp (°C)
Humidity:    master_hum, node1_hum, node2_hum (%)
TVOC (ppm):  master_tvoc, node1_tvoc, node2_tvoc  ← NOW IN PPM
MQ3 (ppm):   master_mq3_ppm, node1_mq3_ppm, node2_mq3_ppm
```

---

## Key Insights from Quality Checks

### High-Temp Regime (34-35°C)
- **Batch1**: Valid until ~102 hours, Batch1 TVOC reaches saturation late
- **batch2**: Completely saturated (both nodes) - **EXCLUDED**
- **batch3**: Well-behaved, manageable saturation
- **Node2** consistently 3-6× more sensitive than Node1

### Low-Temp Regime (18-22°C) 
- **batch4**: Excellent data quality, no saturation
- **batch5**: Aggressive TVOC spike, hits saturation at ~52 hours
- **MQ3 pattern**: Steady increase from baseline

---

## Notebook Structure (Corrected)

| # | Part | Purpose | Output |
|---|------|---------|--------|
| 1 | Setup | Configuration, file paths, constants | ✓ Paths configured |
| 2 | Load | Read CSVs, convert PPB→PPM, normalize | ✓ 1,653 raw rows |
| 3 | Quality | Check MQ3 anomalies, TVOC patterns | ✓ Quality report |
| 4 | Plots | Exploratory time-series (ppm scale) | ✓ 6-panel visualization |
| 5 | Saturation | Quantify cap violations per batch | ✓ Saturation table |
| 6 | Exclusions | Apply rules, identify windows to exclude | ✓ Exclusion summary |
| 7 | Export | Create clean ML-ready CSV in ppm | ✓ 1,140 clean rows |

---

## Units Summary

| Metric | Unit | Notes |
|--------|------|-------|
| Temperature | °C | All nodes and master |
| Humidity | % | All nodes and master |
| **TVOC** | **ppm** | ✓ Converted from ppb (ppb÷1000) |
| MQ3 Ethanol | ppm | Already in ppm (MQ3 native) |
| eCO2 | - | ✗ REMOVED (unreliable) |

---

## Usage

Run cells in order (now properly sequenced):
1. Execute Cell 1 (Setup)
2. Execute Cell 2 (Load) - TVOC auto-converts to ppm
3. Execute Cell 3 (Quality Checks) - inspects MQ3 for anomalies
4. Execute remaining cells for analysis & export

All downstream data in `strawberry_decay_clean_ML_ready.csv` will have **TVOC in ppm**.

---

## Next Steps

- ✓ Notebook structure fixed
- ✓ Unit conversion (PPB → PPM) applied
- ✓ MQ3 quality analysis added
- ☐ Feature engineering (derived features)
- ☐ Train/test split strategy
- ☐ Model baseline training
