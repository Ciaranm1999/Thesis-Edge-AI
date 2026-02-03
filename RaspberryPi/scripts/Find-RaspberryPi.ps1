# Find Raspberry Pi on Network
# Scans the local network to find the Raspberry Pi

Write-Host "=== Finding Raspberry Pi ===" -ForegroundColor Cyan
Write-Host ""

# Get local IP to determine subnet
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -and $_.PrefixOrigin -eq "Dhcp"}).IPAddress

if ($localIP) {
    $subnet = $localIP.Substring(0, $localIP.LastIndexOf('.'))
    Write-Host "Your PC IP: $localIP" -ForegroundColor Green
    Write-Host "Scanning subnet: $subnet.0/24" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This will take about 30-60 seconds..." -ForegroundColor Cyan
    Write-Host ""
    
    $found = @()
    
    # Quick parallel ping scan
    1..254 | ForEach-Object -Parallel {
        $ip = "$using:subnet.$_"
        $ping = Test-Connection -ComputerName $ip -Count 1 -TimeoutSeconds 1 -Quiet -ErrorAction SilentlyContinue
        if ($ping) {
            [PSCustomObject]@{
                IP = $ip
                Online = $true
            }
        }
    } -ThrottleLimit 50 | ForEach-Object {
        Write-Host "[FOUND] $($_.IP) is online" -ForegroundColor Green
        $found += $_.IP
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Found $($found.Count) active devices" -ForegroundColor Yellow
    Write-Host ""
    
    if ($found.Count -gt 0) {
        Write-Host "Try connecting to each one:" -ForegroundColor Green
        foreach ($ip in $found) {
            Write-Host "  ssh edgeai@$ip" -ForegroundColor White
        }
        Write-Host ""
        
        # Try common Raspberry Pi usernames
        $tryIP = Read-Host "Enter IP to try connecting (or press Enter to skip)"
        if ($tryIP) {
            Write-Host ""
            Write-Host "Trying: ssh edgeai@$tryIP" -ForegroundColor Cyan
            ssh edgeai@$tryIP
        }
    } else {
        Write-Host "No devices found. Make sure:" -ForegroundColor Red
        Write-Host "  1. Raspberry Pi is powered on" -ForegroundColor Yellow
        Write-Host "  2. It's connected to the same WiFi network" -ForegroundColor Yellow
        Write-Host "  3. Wait 2 minutes after boot for WiFi to connect" -ForegroundColor Yellow
    }
} else {
    Write-Host "Could not determine local network. Are you connected to WiFi?" -ForegroundColor Red
}
