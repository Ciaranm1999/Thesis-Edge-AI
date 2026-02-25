# Repository Organization Plan

## Current Issues
- Too many MD files in `RaspberryPi/docs/` (10 files)
- Some overlap and redundancy
- No clear hierarchy for new users

## Proposed Structure

```
Thesis-Edge-AI/
├── README.md                          # Main project overview (KEEP - updated)
├── docs/                              # Project-wide documentation
│   ├── RASPBERRY_PI_SETUP_COMPLETE.md # Your completed setup (KEEP)
│   └── GETTING_STARTED.md             # New: Quick start for whole system
│
├── ESP32/
│   ├── README.md                      # ESP32 overview
│   └── docs/
│       └── OVERNIGHT_STABILITY_SUMMARY.md
│
├── RaspberryPi/
│   ├── README.md                      # Pi overview (KEEP - updated)
│   ├── docs/
│   │   ├── setup/                     # Setup guides
│   │   │   ├── QUICK_START.md         # 5-min setup for working system
│   │   │   ├── FIRST_TIME_SETUP.md    # Complete fresh setup
│   │   │   ├── UART_SETUP_GUIDE.md    # Hardware wiring
│   │   │   └── SSH_SETUP.md           # SSH configuration
│   │   │
│   │   ├── guides/                    # Usage guides
│   │   │   ├── RUN_TESTS.md           # Testing hardware
│   │   │   └── SETUP_AND_DATA_GUIDE.md # Data collection guide
│   │   │
│   │   └── archive/                   # Old/deprecated docs
│   │       ├── RASPBERRY_PI_LITE_SETUP.md  # Old OS version
│   │       ├── WIFI_AP_SETUP.md       # Not used
│   │       ├── MIGRATION_GUIDE.md     # One-time migration
│   │       └── mqtt/                  # Old MQTT system
│   │           ├── README_MQTT.md
│   │           └── MQTT_SETUP_GUIDE.md
│   │
│   ├── scripts/                       # Working scripts
│   │   ├── uart_data_collector.py
│   │   ├── Download-PiData.ps1
│   │   └── Start-Batch2.ps1
│   │
│   └── analysis/                      # Jupyter notebooks
│       ├── batch_analysis.ipynb
│       └── energy_analysis.ipynb
```

## Recommended .gitignore Additions

```ignore
# Existing (good):
*.jpg, *.jpeg, *.png          # Images
RaspberryPi/RaspberryPiData/  # All collected data
*.csv                          # Sensor data
*.log                          # Logs

# Add these:
temp_images/                   # Your downloaded temp images
*.ipynb_checkpoints/          # Already done
**/node_modules/              # If you add any JS tools
**/.pytest_cache/             # Python test cache
**/.mypy_cache/               # Python type checking
*.pyc                          # Already covered by *.py[cod]

# ESP32 build outputs (if not already ignored)
ESP32/.pio/                    # PlatformIO build
ESP32/lib/                     # Libraries (if local)
ESP32/.vscode/                 # Already covered

# Analysis outputs
**/plots/                      # Generated plots
**/figures/                    # Generated figures
**/*_analysis_output.*         # Analysis results
```

## Merging to Main Branch Plan

### Option 1: Merge RaspPI → main (Recommended)
```powershell
# Switch to main and merge
git checkout main
git pull origin main           # Get latest main
git merge RaspPI              # Merge RaspPI into main
git push origin main          # Push updated main

# Switch back to continue work
git checkout RaspPI
```

### Option 2: Update main to match RaspPI exactly
```powershell
# Make main identical to RaspPI
git checkout main
git reset --hard RaspPI
git push origin main --force  # ⚠️ Force push (use with caution)

# Switch back
git checkout RaspPI
```

**Recommendation:** Use Option 1 (merge) unless main branch is outdated and you want to replace it entirely.

## Files That Could Be Ignored

### Currently tracked but could be ignored:
1. **Test data in RaspberryPiData/** - Already ignored ✓
2. **Temporary notebooks** - Create `notebooks/scratch/` folder for experiments
3. **Build artifacts** - Already covered
4. **Local configuration** - Add `.env` files pattern

### Suggested new .gitignore entries:
```ignore
# Development/testing
**/scratch/
**/experiments/
**/test_outputs/
.env
.env.local

# Documentation builds (if you add sphinx/mkdocs later)
**/docs/_build/
**/site/

# macOS
.DS_Store
.AppleDouble
.LSOverride

# Windows
Thumbs.db        # Already there
Desktop.ini
$RECYCLE.BIN/
```

## Action Items

1. ✅ Reorganize docs into setup/, guides/, archive/
2. ✅ Update .gitignore with new patterns
3. ✅ Create GETTING_STARTED.md for newcomers
4. ✅ Merge RaspPI to main
5. ✅ Continue working on RaspPI branch
6. ✅ Archive outdated/redundant docs

## Priority MD Files to Keep in Main Locations

**Essential (active use):**
- README.md (root)
- RaspberryPi/README.md
- RaspberryPi/docs/setup/QUICK_START.md
- RaspberryPi/docs/setup/UART_SETUP_GUIDE.md
- docs/RASPBERRY_PI_SETUP_COMPLETE.md (your working config)

**Archive (reference only):**
- Everything in archive/ subdirectories
