# Download Batch Data from Raspberry Pi
# This script downloads sensor data and images for a specific batch
# Usage: .\Download-BatchData.ps1 -BatchName "batch3"

param(
    [Parameter(Mandatory=$false)]
    [string]$BatchName,
    
    [Parameter(Mandatory=$false)]
    [string]$PiIP = "172.20.10.3",
    
    [Parameter(Mandatory=$false)]
    [string]$PiUser = "edgeai",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipImages,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipCSV
)

# Get script directory and calculate paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$LOCAL_DATA_DIR = Join-Path $RepoRoot "RaspberryPiData"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Batch Data Download from Raspberry Pi      ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# If no batch specified, list available batches on Pi and prompt
if (-not $BatchName) {
    Write-Host "Checking available batches on Pi..." -ForegroundColor Yellow
    Write-Host ""
    
    $availableBatches = ssh ${PiUser}@${PiIP} "ls -d ~/thesis_data/sensor_data/*/ 2>/dev/null | xargs -n 1 basename" 2>$null
    
    if ($availableBatches) {
        Write-Host "Available batches on Pi:" -ForegroundColor Green
        $availableBatches | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
        Write-Host ""
        $BatchName = Read-Host "Enter batch name to download (e.g., batch2, batch3)"
    } else {
        Write-Host "❌ Could not connect to Pi or no batches found" -ForegroundColor Red
        Write-Host "Using default batch name. You can specify with -BatchName parameter" -ForegroundColor Yellow
        $BatchName = Read-Host "Enter batch name to download"
    }
}

if (-not $BatchName) {
    Write-Host "❌ No batch name provided. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Batch: $BatchName" -ForegroundColor Cyan
Write-Host "🌐 Pi IP: $PiIP" -ForegroundColor Cyan
Write-Host "👤 User: $PiUser" -ForegroundColor Cyan
Write-Host ""

# Create local directories
$BatchImageDir = Join-Path $LOCAL_DATA_DIR "images\$BatchName"
$BatchSensorDir = Join-Path $LOCAL_DATA_DIR "sensor_data\$BatchName"

Write-Host "Creating local directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $BatchImageDir | Out-Null
New-Item -ItemType Directory -Force -Path $BatchSensorDir | Out-Null
Write-Host "✓ Directories ready" -ForegroundColor Green
Write-Host ""

# Download sensor data CSV
if (-not $SkipCSV) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "📊 Downloading sensor data CSV..." -ForegroundColor Yellow
    Write-Host ""
    
    Push-Location $BatchSensorDir
    try {
        $csvResult = scp "${PiUser}@${PiIP}:~/thesis_data/sensor_data/$BatchName/unified_sensor_data.csv" "unified_sensor_data.csv" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $csvFile = Get-Item "unified_sensor_data.csv" -ErrorAction SilentlyContinue
            if ($csvFile) {
                $csvRows = (Get-Content "unified_sensor_data.csv").Count - 1
                Write-Host "✓ Downloaded CSV: $([math]::Round($csvFile.Length/1KB, 2)) KB, $csvRows data rows" -ForegroundColor Green
            }
        } else {
            Write-Host "❌ Failed to download CSV" -ForegroundColor Red
            Write-Host "   Make sure the file exists at: ~/thesis_data/sensor_data/$BatchName/unified_sensor_data.csv" -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
    Write-Host ""
}

# Download images
if (-not $SkipImages) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "📸 Downloading images..." -ForegroundColor Yellow
    Write-Host ""
    
    # First check how many images exist
    $imageCount = ssh ${PiUser}@${PiIP} "ls ~/thesis_data/images/$BatchName/*.jpg 2>/dev/null | wc -l" 2>$null
    
    if ($imageCount -and $imageCount -gt 0) {
        Write-Host "   Found $imageCount images on Pi" -ForegroundColor Cyan
        Write-Host "   This may take a few minutes..." -ForegroundColor Yellow
        Write-Host ""
        
        Push-Location $BatchImageDir
        try {
            scp "${PiUser}@${PiIP}:~/thesis_data/images/$BatchName/*.jpg" . 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                $localImages = Get-ChildItem "*.jpg" -ErrorAction SilentlyContinue
                Write-Host "✓ Downloaded $($localImages.Count) images" -ForegroundColor Green
                
                if ($localImages.Count -gt 0) {
                    $totalSize = ($localImages | Measure-Object -Property Length -Sum).Sum
                    Write-Host "   Total size: $([math]::Round($totalSize/1MB, 2)) MB" -ForegroundColor Cyan
                }
            } else {
                Write-Host "❌ Failed to download images" -ForegroundColor Red
            }
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "⚠️  No images found at: ~/thesis_data/images/$BatchName/" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 Download Summary" -ForegroundColor Cyan
Write-Host ""

$csvFile = Get-ChildItem "$BatchSensorDir\*.csv" -ErrorAction SilentlyContinue
$imageFiles = Get-ChildItem "$BatchImageDir\*.jpg" -ErrorAction SilentlyContinue

Write-Host "Batch: $BatchName" -ForegroundColor White
Write-Host "  CSV files:  $($csvFile.Count)" -ForegroundColor White
Write-Host "  Images:     $($imageFiles.Count)" -ForegroundColor White
Write-Host ""
Write-Host "Saved to:" -ForegroundColor Cyan
Write-Host "  $LOCAL_DATA_DIR" -ForegroundColor White
Write-Host ""

if ($csvFile.Count -eq 0 -and $imageFiles.Count -eq 0) {
    Write-Host "⚠️  No data was downloaded. Please check:" -ForegroundColor Yellow
    Write-Host "   1. Pi is connected (IP: $PiIP)" -ForegroundColor Yellow
    Write-Host "   2. Batch name is correct: $BatchName" -ForegroundColor Yellow
    Write-Host "   3. Data exists on Pi in: ~/thesis_data/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To list batches on Pi, run:" -ForegroundColor Cyan
    Write-Host "   ssh ${PiUser}@${PiIP} 'ls ~/thesis_data/sensor_data/'" -ForegroundColor White
} else {
    Write-Host "✅ Download complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Open batch_analysis.ipynb in Jupyter" -ForegroundColor White
    Write-Host "  2. Set SINGLE_BATCH = `"$BatchName`"" -ForegroundColor White
    Write-Host "  3. Update BATCHES configuration if needed" -ForegroundColor White
    Write-Host "  4. Run all cells to analyze data" -ForegroundColor White
}

Write-Host ""
