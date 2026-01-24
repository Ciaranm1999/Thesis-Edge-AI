# Quick SSH Connection Script for Raspberry Pi
# Save this as: Connect-RaspberryPi.ps1

Write-Host "=== Raspberry Pi SSH Connection Helper ===" -ForegroundColor Cyan
Write-Host ""

# Common Raspberry Pi IP ranges to scan
$commonIPs = @(
    "192.168.1.x",
    "192.168.0.x",
    "10.0.0.x"
)

Write-Host "Step 1: Find your Raspberry Pi IP address" -ForegroundColor Yellow
Write-Host ""
Write-Host "Common network ranges:" -ForegroundColor Green
$commonIPs | ForEach-Object { Write-Host "  - $_" }
Write-Host ""

Write-Host "Option 1: Scan for Raspberry Pi (requires arp command)" -ForegroundColor Yellow
$subnet = Read-Host "Enter your network subnet (e.g., 192.168.1)"

if ($subnet) {
    Write-Host "Scanning $subnet.0/24 network..." -ForegroundColor Cyan
    
    # Quick ping sweep
    1..254 | ForEach-Object {
        $ip = "$subnet.$_"
        $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -ErrorAction SilentlyContinue
        if ($ping) {
            Write-Host "[FOUND] $ip is responding" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "Step 2: Connect to Raspberry Pi" -ForegroundColor Yellow
$piIP = Read-Host "Enter Raspberry Pi IP address"

if ($piIP) {
    Write-Host ""
    Write-Host "Attempting to connect to pi@$piIP..." -ForegroundColor Cyan
    Write-Host "Default password is: raspberry" -ForegroundColor Yellow
    Write-Host ""
    
    ssh pi@$piIP
}
else {
    Write-Host "No IP address provided. Exiting." -ForegroundColor Red
}
