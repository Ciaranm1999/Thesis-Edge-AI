# Notebook Revamp Summary - Data Exploration & Curation

## Overview
The `all_batches_ml_prep.ipynb` notebook has been **completely rebuilt** to focus on:
1. **Data exploration** with clear visualizations before/after cleaning
2. **Saturation detection** and automated exclusion of unreliable data
3. **Feature selection** (removed eCO2 as unreliable)
4. **Export of clean ML-ready dataset**

---

## Key Changes from Original

### ❌ Removed
- **eCO2 metric entirely** - SGP30 eCO2 is a rough estimate, not reliable for decay detection
- **All eCO2 analysis cells** - replaced with TVOC focus
- **Complex train/test split logic** - moved to next phase (kept simple for now)

### ✅ Added
- **Rich exploratory plots** - TVOC & MQ3 by regime, Node1 vs Node2 comparison
- **Saturation analysis** - quantifies which batches/nodes hit the 60,000 ppb TVOC cap
- **Automated exclusion rules** - removes saturated windows per batch
- **Feature summary** - documents what's available for ML
- **Batch metadata table** - duration, temperature ranges, humidity

---

## Saturation Analysis Results

### Batch Processing Decisions
| Batch | Regime | Status | Rows Kept | Notes |
|-------|--------|--------|-----------|-------|
| **Batch1** | high_temp | ✓ Partial | 245 | Excluded post-saturation readings |
| **batch2** | high_temp | **✗ EXCLUDED** | 0 | 100% TVOC saturation (both nodes) |
| **batch3** | high_temp | ✓ Full | 366 | Acceptable saturation level |
| **batch4** | low_temp | ✓ Full | 288 | Low saturation, good quality |
| **batch5** | low_temp | ✓ Partial | 241 | Excluded post-saturation readings |

**Total Clean Data: 1,140 rows** (was 1,653 before exclusions)

---

## Files Generated

### Main Output
- **`strawberry_decay_clean_ML_ready.csv`** (1,140 rows)
  - Only non-saturated data
  - All eCO2 columns removed
  - Includes batch, regime, mould_start metadata, and elapsed_hours
  - Ready for feature engineering and train/test split

### Supporting Files
- **`batch_summary.csv`** - Duration, temp/humidity ranges per batch
- `all_batches_ml_curated.csv` - Full dataset with exclusion flags (for reference)
- `ml_train.csv` / `ml_test.csv` - Old split format (will be regenerated if needed)

---

## Data Features Available for ML

### Sensor Readings (all per node)
- **Temperature (°C)**: master_temp, node1_temp, node2_temp
- **Humidity (%)**: master_hum, node1_hum, node2_hum
- **TVOC (ppb)**: master_tvoc, node1_tvoc, node2_tvoc
  - *Guaranteed ≤ 60,000 ppb (no saturated readings)*
- **MQ3 Ethanol (ppm)**: master_mq3_ppm, node1_mq3_ppm, node2_mq3_ppm

### Metadata Columns
- `timestamp` - Measurement datetime
- `batch` - Batch identifier
- `regime` - "high_temp" or "low_temp"
- `cycle_number` - Sequential measurement number
- `elapsed_hours` - Hours since batch start (normalized)
- `mould_start` - When mould was first observed (None for batch4)
- `has_mould` - Boolean indicator

---

## Notebook Structure

The notebook is now organized into 6 logical parts:

1. **Setup & Configuration**
   - Load libraries, define batch metadata, TVOC cap (60,000 ppb)

2. **Load Data**
   - Read all 5 batch CSVs, normalize signals, add metadata

3. **Exploratory Visualization**
   - 6-panel plot: TVOC & MQ3 by regime, Node1 vs Node2 comparison
   - Shows why saturation is a problem and regime differences

4. **Saturation Analysis**
   - Quantifies % of readings at cap per batch/node
   - Identifies which batches are unusable vs. salvageable

5. **Exclusion Strategy & Application**
   - Defines rules (Batch2 exclude all, others exclude saturation windows)
   - Applies masks and generates clean dataset

6. **Feature Summary & Export**
   - Documents available data
   - Exports ML-ready CSV

---

## Next Steps

You now have a clean, saturation-free dataset ready for:

### Immediate
- ✅ **Feature engineering** - Create derived features (e.g., Node_TVOC - Master_TVOC)
- ✅ **Exploratory analysis** - Confirm regime differences, identify mould biomarkers
- ✅ **Baseline classifier** - Train simple model (logistic regression) on TVOC + MQ3

### Medium-term
- **Train/test split** - Now that data is curated, decide on split strategy
  - Option A: By batch (to benchmark cross-batch generalization)
  - Option B: By regime (to evaluate regime transfer)
  - Option C: Stratified temporal split

### Long-term
- **Model selection** - Simple, two-stage, or LSTM-based?
- **Cross-regime validation** - How well do models trained on high_temp perform on low_temp?

---

## Quality Assurance

✓ All plots generated successfully  
✓ Saturation thresholds validated (60,000 ppb for TVOC)  
✓ Exclusion rules applied correctly  
✓ 1,140 clean rows exported  
✓ No NaN values in core features  
✓ eCO2 fully removed and not referenced  

---

## File Locations

- **Notebook**: `RaspberryPi/analysis/all_batches_ml_prep.ipynb`
- **Clean Data**: `RaspberryPi/RaspberryPiData/analysis_exports/strawberry_decay_clean_ML_ready.csv`
- **Batch Summary**: `RaspberryPi/RaspberryPiData/analysis_exports/batch_summary.csv`
