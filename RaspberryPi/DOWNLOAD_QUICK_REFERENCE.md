# 📥 BATCH DATA DOWNLOAD - QUICK REFERENCE

## 🚀 One-Line Download

```powershell
.\Download-BatchData.ps1 -BatchName "batch3"
```

## 📋 Manual Download Steps

### 1. Create Directories
```powershell
$BATCH = "batch3"
$BASE = "c:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Code\Thesis-Edge-AI\RaspberryPi\RaspberryPiData"
New-Item -ItemType Directory -Force -Path "$BASE\images\$BATCH"
New-Item -ItemType Directory -Force -Path "$BASE\sensor_data\$BATCH"
```

### 2. Download CSV
```powershell
cd "$BASE\sensor_data\$BATCH"
scp edgeai@172.20.10.3:~/thesis_data/sensor_data/$BATCH/unified_sensor_data.csv .
```

### 3. Download Images
```powershell
cd "$BASE\images\$BATCH"
scp "edgeai@172.20.10.3:~/thesis_data/images/$BATCH/*.jpg" .
```

### 4. Verify
```powershell
(Get-Content "$BASE\sensor_data\$BATCH\unified_sensor_data.csv").Count
(Get-ChildItem "$BASE\images\$BATCH\*.jpg").Count
```

## ⚙️ Update Analysis Notebook

In `batch_analysis.ipynb`:
```python
BATCHES = {
    "batch3": {
        "mould_start": None,  # Update when detected
        "color": "#70ad47",
        "description": "Third batch - description here"
    }
}

SINGLE_BATCH = "batch3"
```

## 🔍 Troubleshooting

**Can't connect to Pi:**
```powershell
Test-Connection 172.20.10.3
ipconfig | Select-String "IPv4"
```

**Check what's on Pi:**
```powershell
ssh edgeai@172.20.10.3 'ls ~/thesis_data/sensor_data/'
ssh edgeai@172.20.10.3 'ls ~/thesis_data/images/batch2/*.jpg | wc -l'
```

**Partial download:**
- Just re-run the scp command
- Files will be overwritten/resumed

---
📖 Full Guide: `docs/guides/DOWNLOAD_BATCH_DATA.md`  
🤖 Script: `scripts/Download-BatchData.ps1`
