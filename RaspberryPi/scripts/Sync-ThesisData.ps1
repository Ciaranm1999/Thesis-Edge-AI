# Data Sync Script - Copy thesis data from Raspberry Pi to Windows laptop
# Run this whenever you want to download the latest data

param(
    [string]$PiIP = "192.168.2.84",
    [string]$PiUser = "edgeai",
    [string]$LocalPath = "$HOME\Desktop\thesis_data"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Thesis Data Sync from Raspberry Pi" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create local directory if it doesn't exist
if (!(Test-Path $LocalPath)) {
    New-Item -ItemType Directory -Path $LocalPath -Force | Out-Null
    Write-Host "Created local directory: $LocalPath" -ForegroundColor Green
}

# Test connection
Write-Host "Testing connection to Pi..." -ForegroundColor Yellow
$testConnection = Test-NetConnection -ComputerName $PiIP -Port 22 -InformationLevel Quiet

if (!$testConnection) {
    Write-Host "✗ Cannot reach Raspberry Pi at $PiIP" -ForegroundColor Red
    Write-Host "  Make sure the Pi is powered on and connected to network" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Pi is reachable" -ForegroundColor Green
Write-Host ""

# Sync sensor data
Write-Host "Syncing sensor data..." -ForegroundColor Yellow
scp -r "${PiUser}@${PiIP}:~/thesis_data/sensor_data" "$LocalPath\"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Sensor data synced" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to sync sensor data" -ForegroundColor Red
}

Write-Host ""

# Sync images
Write-Host "Syncing images..." -ForegroundColor Yellow
scp -r "${PiUser}@${PiIP}:~/thesis_data/images" "$LocalPath\"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Images synced" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to sync images" -ForegroundColor Red
}

Write-Host ""

# Sync logs
Write-Host "Syncing logs..." -ForegroundColor Yellow
scp "${PiUser}@${PiIP}:~/thesis_data/data_collector.log" "$LocalPath\"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Logs synced" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to sync logs" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sync Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Data location: $LocalPath" -ForegroundColor Green
Write-Host ""

# Show summary
$csvFiles = Get-ChildItem -Path "$LocalPath\sensor_data" -Filter "*.csv" -ErrorAction SilentlyContinue
$imageFiles = Get-ChildItem -Path "$LocalPath\images" -Filter "*.jpg" -ErrorAction SilentlyContinue

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  CSV files: $($csvFiles.Count)" -ForegroundColor White
Write-Host "  Images: $($imageFiles.Count)" -ForegroundColor White

if ($csvFiles.Count -gt 0) {
    $latestCsv = $csvFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host "  Latest CSV: $($latestCsv.Name)" -ForegroundColor White
}

if ($imageFiles.Count -gt 0) {
    $latestImage = $imageFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host "  Latest image: $($latestImage.Name)" -ForegroundColor White
}

Write-Host ""
Write-Host "To open the folder:" -ForegroundColor Yellow
Write-Host "  explorer `"$LocalPath`"" -ForegroundColor White
Write-Host ""

# Ask if user wants to open the folder
$response = Read-Host "Open data folder now? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    explorer "$LocalPath"
}
