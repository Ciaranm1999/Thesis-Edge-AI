# Download Data from Raspberry Pi
# Quick script to copy sensor data and images from Pi to laptop

$PI_IP = "172.20.10.3"
$PI_USER = "edgeai"
$LOCAL_DATA_DIR = "c:\Users\cmahe\OneDrive\Desktop\SSE Masters\Thesis\Data"

Write-Host "=== Downloading Data from Raspberry Pi ===" -ForegroundColor Cyan
Write-Host ""

# Create local download directory
New-Item -ItemType Directory -Force -Path $LOCAL_DATA_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL_DATA_DIR\sensor_data" | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL_DATA_DIR\images" | Out-Null
New-Item -ItemType Directory -Force -Path "$LOCAL_DATA_DIR\logs" | Out-Null

Write-Host "Downloading sensor data CSV..." -ForegroundColor Yellow
scp ${PI_USER}@${PI_IP}:~/thesis_data/sensor_data/*.csv "$LOCAL_DATA_DIR\sensor_data\"

Write-Host "Downloading images..." -ForegroundColor Yellow
scp ${PI_USER}@${PI_IP}:~/thesis_data/images/*.jpg "$LOCAL_DATA_DIR\images\"

Write-Host "Downloading logs..." -ForegroundColor Yellow
scp ${PI_USER}@${PI_IP}:~/thesis_data/*.log "$LOCAL_DATA_DIR\logs\"

Write-Host ""
Write-Host "Download complete!" -ForegroundColor Green
Write-Host "Data saved to: $LOCAL_DATA_DIR" -ForegroundColor Green
Write-Host ""

# Show summary
$csvFiles = Get-ChildItem "$LOCAL_DATA_DIR\sensor_data\*.csv" -ErrorAction SilentlyContinue
$imageFiles = Get-ChildItem "$LOCAL_DATA_DIR\images\*.jpg" -ErrorAction SilentlyContinue
$logFiles = Get-ChildItem "$LOCAL_DATA_DIR\logs\*.log" -ErrorAction SilentlyContinue

Write-Host "Downloaded:" -ForegroundColor Cyan
Write-Host "  - CSV files: $($csvFiles.Count)" -ForegroundColor White
Write-Host "  - Images: $($imageFiles.Count)" -ForegroundColor White
Write-Host "  - Log files: $($logFiles.Count)" -ForegroundColor White

if ($csvFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Latest CSV:" -ForegroundColor Cyan
    $latest = $csvFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host "  $($latest.Name) - $([math]::Round($latest.Length/1KB, 2)) KB" -ForegroundColor White
}

if ($imageFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Latest image:" -ForegroundColor Cyan
    $latestImg = $imageFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host "  $($latestImg.Name) - $([math]::Round($latestImg.Length/1KB, 2)) KB" -ForegroundColor White
}

Write-Host ""
