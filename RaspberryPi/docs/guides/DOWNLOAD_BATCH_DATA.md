# How to Download Batch Data from Raspberry Pi

This guide explains the standardized process for downloading sensor data and images for each experimental batch.

## Quick Start

### Method 1: Using the Automated Script (Recommended)

```powershell
# Navigate to the scripts directory
cd RaspberryPi\scripts

# Download a specific batch (interactive)
.\Download-BatchData.ps1

# Or specify the batch name directly
.\Download-BatchData.ps1 -BatchName "batch3"
```

### Method 2: Manual Download (If Script Fails)

If you need to download manually, follow these exact steps:

#### 1. Ensure Pi is Connected
```powershell
# Check your local IP (should be 172.20.10.2 on phone hotspot)
ipconfig | Select-String "IPv4" -Context 2

# Test connection to Pi
Test-Connection -ComputerName 172.20.10.3 -Count 2
```

#### 2. Create Local Directories
```powershell
# Set the batch name
$BATCH = "batch3"  # Change this for each batch

# Create directories
$BASE = "c:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Code\Thesis-Edge-AI\RaspberryPi\RaspberryPiData"
New-Item -ItemType Directory -Force -Path "$BASE\images\$BATCH"
New-Item -ItemType Directory -Force -Path "$BASE\sensor_data\$BATCH"
```

#### 3. Download Sensor Data CSV
```powershell
cd "$BASE\sensor_data\$BATCH"
scp edgeai@172.20.10.3:~/thesis_data/sensor_data/$BATCH/unified_sensor_data.csv unified_sensor_data.csv
```

**Expected result:** File downloads showing progress, ~60-100KB for a few days of data

#### 4. Download Images
```powershell
cd "$BASE\images\$BATCH"
scp "edgeai@172.20.10.3:~/thesis_data/images/$BATCH/*.jpg" .
```

**Expected result:** 
- Downloads all .jpg files (typically 50-150 images)
- Takes 2-5 minutes depending on image count
- Each image is ~0.5-2 MB

#### 5. Verify Download
```powershell
# Check CSV
$csvRows = (Get-Content "$BASE\sensor_data\$BATCH\unified_sensor_data.csv").Count
Write-Host "CSV has $csvRows rows (including header)"

# Check images
$imgCount = (Get-ChildItem "$BASE\images\$BATCH\*.jpg").Count
Write-Host "Downloaded $imgCount images"
```

## Directory Structure

The data should be organized as follows:

```
RaspberryPiData/
├── images/
│   ├── Batch1/
│   │   └── capture_*.jpg
│   ├── batch2/
│   │   └── capture_*.jpg
│   └── batch3/
│       └── capture_*.jpg
└── sensor_data/
    ├── Batch1/
    │   └── unified_sensor_data.csv
    ├── batch2/
    │   └── unified_sensor_data.csv
    └── batch3/
        └── unified_sensor_data.csv
```

⚠️ **Important Naming Convention:**
- Use consistent batch naming (Batch1, batch2, batch3, etc.)
- The script handles case-sensitive names automatically
- Keep the exact name format from the Pi

## Batch Naming Guidelines

When starting a new batch:

1. **On the Pi:** Data is stored in `~/thesis_data/`
   - Sensor CSV: `~/thesis_data/sensor_data/batch#/unified_sensor_data.csv`
   - Images: `~/thesis_data/images/batch#/*.jpg`

2. **Locally:** Use the same batch name
   - Example: If Pi has `batch3`, download to local `batch3` folder

3. **In Analysis Notebook:** Update configuration
   ```python
   # In batch_analysis.ipynb, Cell 1
   BATCHES = {
       "Batch1": {...},
       "batch2": {...},
       "batch3": {  # Add new batch
           "mould_start": None,  # Update when detected
           "color": "#70ad47",
           "description": "Third batch - your description"
       }
   }
   
   SINGLE_BATCH = "batch3"  # For single-batch analysis
   ```

## Troubleshooting

### Connection Issues
```powershell
# If connection fails, check Pi IP
ssh edgeai@172.20.10.3 'hostname -I'

# Try different IP if needed (common alternatives)
# - 172.20.10.3 (phone hotspot)
# - 192.168.1.X (home network)
```

### Authentication Prompts
- You'll be asked for password multiple times (once per scp command)
- Password is your Pi user password (default: what you set for `edgeai`)
- Consider setting up SSH keys to avoid repeated passwords

### No Data Found
```powershell
# Check what batches exist on Pi
ssh edgeai@172.20.10.3 'ls ~/thesis_data/sensor_data/'

# Check image count for a batch
ssh edgeai@172.20.10.3 'ls ~/thesis_data/images/batch2/*.jpg | wc -l'
```

### Partial Download (Images Stopped Mid-Transfer)
```powershell
# Check what was downloaded
Get-ChildItem "$BASE\images\$BATCH\*.jpg" | Measure-Object

# Restart download - scp will resume/overwrite
cd "$BASE\images\$BATCH"
scp "edgeai@172.20.10.3:~/thesis_data/images/$BATCH/*.jpg" .
```

## Pre-Analysis Checklist

Before running analysis on a new batch:

- [ ] CSV downloaded and contains data rows
- [ ] Images downloaded (count matches Pi)
- [ ] Batch added to `BATCHES` dict in notebook
- [ ] `SINGLE_BATCH` set to new batch name
- [ ] `mould_start` timestamp updated (if mould detected)
- [ ] `description` added for the batch

## Script Parameters

The `Download-BatchData.ps1` script accepts these parameters:

```powershell
.\Download-BatchData.ps1 `
    -BatchName "batch3" `      # Required: batch folder name
    -PiIP "172.20.10.3" `      # Optional: Pi IP address  
    -PiUser "edgeai" `         # Optional: SSH username
    -SkipImages `              # Optional: download CSV only
    -SkipCSV                   # Optional: download images only
```

Examples:
```powershell
# Download only CSV (fast preview)
.\Download-BatchData.ps1 -BatchName "batch3" -SkipImages

# Download only images (if CSV already downloaded)
.\Download-BatchData.ps1 -BatchName "batch3" -SkipCSV

# Download from different Pi IP
.\Download-BatchData.ps1 -BatchName "batch3" -PiIP "192.168.1.100"
```

## Next Steps After Download

1. Open `batch_analysis.ipynb`
2. Update configuration for the new batch
3. Run analysis cells
4. Review plots and data quality
5. Document any observations in the notebook

---

**Last Updated:** March 3, 2026  
**Maintained By:** Thesis Project
