# Start Batch2 Data Collection on Raspberry Pi
# This script:
# 1. Copies the updated uart_data_collector.py to the Pi
# 2. Restarts the data collection service for batch2

$PI_IP = "172.20.10.3"  # iPhone hotspot IP
$PI_USER = "edgeai"

Write-Host "=== Starting Batch2 Data Collection ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Copy updated script to Pi
Write-Host "Step 1: Copying updated data collector script to Pi..." -ForegroundColor Yellow
scp ".\RaspberryPi\scripts\uart_data_collector.py" "${PI_USER}@${PI_IP}:~/Thesis-Edge-AI/RaspberryPi/scripts/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to copy script. Check SSH connection." -ForegroundColor Red
    exit 1
}
Write-Host "Script copied successfully!" -ForegroundColor Green
Write-Host ""

# Step 2: SSH commands to restart service
Write-Host "Step 2: Connecting to Pi to restart data collection..." -ForegroundColor Yellow
Write-Host ""

# Create SSH command string
$sshCommands = @"
echo '=== Stopping current data collection service ===' &&
sudo systemctl stop thesis-data-collector &&
echo 'Service stopped.' &&
echo '' &&
echo '=== Starting batch2 data collection ===' &&
export TEST_ID=batch2 &&
cd ~/Thesis-Edge-AI/RaspberryPi/scripts &&
nohup python3 uart_data_collector.py > ~/thesis_data/batch2.log 2>&1 &
echo 'Batch2 collection started!' &&
echo '' &&
echo 'Checking if process is running...' &&
sleep 2 &&
ps aux | grep uart_data_collector | grep -v grep &&
echo '' &&
echo '=== Setup Complete ===' &&
echo 'Data will be saved to:' &&
echo '  - ~/thesis_data/sensor_data/batch2/' &&
echo '  - ~/thesis_data/images/batch2/' &&
echo '' &&
echo 'To monitor logs:' &&
echo '  tail -f ~/thesis_data/batch2.log'
"@

# Execute SSH commands
ssh "${PI_USER}@${PI_IP}" $sshCommands

Write-Host ""
Write-Host "Batch2 data collection started!" -ForegroundColor Green
Write-Host ""
Write-Host "To monitor in real-time, run:" -ForegroundColor Cyan
Write-Host "  ssh ${PI_USER}@${PI_IP} 'tail -f ~/thesis_data/batch2.log'" -ForegroundColor White
Write-Host ""
