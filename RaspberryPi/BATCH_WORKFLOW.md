# 🔄 Batch Data Collection Workflow

## Complete Process Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EXPERIMENT WORKFLOW                       │
└─────────────────────────────────────────────────────────────┘

📦 BATCH SETUP
    │
    ├─ 1. Place strawberries in containers
    ├─ 2. Seal containers with sensors (Node1, Node2)
    ├─ 3. Power on ESP32 Master + Nodes
    ├─ 4. Start Raspberry Pi data collection
    └─ 5. Note start timestamp
    
    ↓
    
⏱️ DATA COLLECTION (Running on Pi)
    │
    ├─ UART receives sensor data every 15 min
    ├─ CSV updated: ~/thesis_data/sensor_data/batch#/unified_sensor_data.csv
    ├─ Camera captures image every hour
    ├─ Images saved: ~/thesis_data/images/batch#/capture_*.jpg
    └─ Service auto-runs 24/7
    
    ↓ (After 3-7 days or mould detected)
    
🔚 BATCH END
    │
    ├─ 1. Note end timestamp & mould detection time
    ├─ 2. Stop data collection (optional, or let it run)
    └─ 3. Ready to download for analysis
    
    ↓
    
📥 DOWNLOAD TO LOCAL MACHINE
    │
    ├─ METHOD A: Automated Script (Recommended)
    │   └─> .\Download-BatchData.ps1 -BatchName "batch3"
    │
    └─ METHOD B: Manual SCP Commands
        ├─> Create directories
        ├─> scp CSV file
        └─> scp image files
    
    ↓
    
🔍 VERIFY DOWNLOAD
    │
    ├─ Check CSV row count
    ├─ Check image count vs Pi
    └─ Confirm file sizes reasonable
    
    ↓
    
📊 ANALYSIS (Jupyter Notebook)  
    │
    ├─ 1. Open: RaspberryPi/analysis/batch_analysis.ipynb
    ├─ 2. Update BATCHES configuration
    │   └─> Add new batch metadata
    ├─ 3. Set SINGLE_BATCH = "batch3"
    ├─ 4. Run all cells
    └─ 5. Review:
        ├─ Time series plots
        ├─ Correlation heatmaps
        ├─ Distribution analysis
        ├─ Outlier detection
        └─ Image gallery
    
    ↓
    
📝 DOCUMENT FINDINGS
    │
    ├─ Note mould appearance timestamp
    ├─ Document anomalies or issues
    ├─ Export key plots for thesis
    └─ Save notebook with results
    
    ↓
    
🔄 REPEAT FOR NEXT BATCH
```

## File Locations Quick Reference

### On Raspberry Pi
```
~/thesis_data/
├── sensor_data/
│   ├── Batch1/unified_sensor_data.csv
│   ├── batch2/unified_sensor_data.csv
│   └── batch3/unified_sensor_data.csv
├── images/
│   ├── Batch1/*.jpg
│   ├── batch2/*.jpg
│   └── batch3/*.jpg
└── uart_data_collector.log
```

### On Local Machine
```
Thesis-Edge-AI/RaspberryPi/
├── RaspberryPiData/          ← Downloaded data here
│   ├── images/
│   │   ├── Batch1/
│   │   ├── batch2/
│   │   └── batch3/
│   └── sensor_data/
│       ├── Batch1/
│       ├── batch2/
│       └── batch3/
├── analysis/
│   └── batch_analysis.ipynb  ← Analysis happens here
├── scripts/
│   └── Download-BatchData.ps1 ← Download tool
└── docs/guides/
    └── DOWNLOAD_BATCH_DATA.md ← Detailed instructions
```

## Common Scenarios

### Scenario 1: Starting a New Batch
```
1. On Pi: Data collector auto-creates new batch folders
2. Monitor remotely: ssh edgeai@172.20.10.3
3. Download when ready: .\Download-BatchData.ps1 -BatchName "batch4"
```

### Scenario 2: Partial Data Preview
```
# Download only CSV (fast)
.\Download-BatchData.ps1 -BatchName "batch3" -SkipImages

# Analyze early trends
# Download images later if needed
.\Download-BatchData.ps1 -BatchName "batch3" -SkipCSV
```

### Scenario 3: Multiple Batches Running
```
# Download each batch separately
.\Download-BatchData.ps1 -BatchName "batch3"
.\Download-BatchData.ps1 -BatchName "batch4"

# Compare in multi_batch_comparison.ipynb
```

### Scenario 4: Batch After Cable Disconnect
```
# Data before disconnect already on Pi
# After reconnect, new batch starts automatically
# Download each batch period separately
```

## Automation Tips

### Create Batch Download Aliases
Add to your PowerShell profile:
```powershell
function Get-Batch { 
    param($Name) 
    cd "C:\...\Thesis-Edge-AI\RaspberryPi\scripts"
    .\Download-BatchData.ps1 -BatchName $Name
}

# Usage: Get-Batch batch3
```

### Schedule Regular Backups
```powershell
# Download data daily without images (quick backup)
.\Download-BatchData.ps1 -BatchName "batch3" -SkipImages

# Full download weekly
# (Let experiment run, analyze later)
```

## Data Quality Checklist

Before closing a batch:
- [ ] CSV has expected number of cycles (~96/day for 15min intervals)
- [ ] No large gaps in timestamps
- [ ] Images captured (~24/day for hourly captures)
- [ ] All 3 nodes (master, node1, node2) have data
- [ ] Sensors didn't saturate immediately (unless expected)
- [ ] Mould detection timestamp recorded
- [ ] Notes on any anomalies or manual interventions

## Troubleshooting Decision Tree

```
Can't download data?
├─ Can't connect to Pi?
│  ├─ Check Pi is on: ping 172.20.10.3
│  ├─ Check network: ipconfig
│  └─ Try SSH: ssh edgeai@172.20.10.3
│
├─ Connection OK but no files?
│  ├─ Check batch name: ssh edgeai@172.20.10.3 'ls ~/thesis_data/sensor_data/'
│  ├─ Verify service running: systemctl status thesis-uart-collector
│  └─ Check logs: tail ~/thesis_data/uart_data_collector.log
│
└─ Partial download?
   └─ Re-run same command (scp resumes/overwrites)
```

---

**Quick Links:**
- 📖 [Detailed Download Guide](docs/guides/DOWNLOAD_BATCH_DATA.md)
- 🚀 [Quick Reference](DOWNLOAD_QUICK_REFERENCE.md)
- 📊 [Analysis Notebook](analysis/batch_analysis.ipynb)
- ⚙️ [Download Script](scripts/Download-BatchData.ps1)
