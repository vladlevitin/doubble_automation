# Android Emulator Launcher Script
# This script helps you launch Android emulators easily

Write-Host "=== Android Emulator Launcher ===" -ForegroundColor Cyan
Write-Host ""

# Set emulator path
$emulatorPath = "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"

# Check if emulator exists
if (-not (Test-Path $emulatorPath)) {
    Write-Host "ERROR: Android emulator not found at: $emulatorPath" -ForegroundColor Red
    Write-Host "Please install Android Studio and set up an emulator first." -ForegroundColor Yellow
    exit 1
}

# List available emulators
Write-Host "Available Emulators:" -ForegroundColor Green
$avds = & $emulatorPath -list-avds
$avdList = @()
$index = 1
foreach ($avd in $avds) {
    Write-Host "  [$index] $avd" -ForegroundColor White
    $avdList += $avd
    $index++
}

Write-Host ""

# Check if any emulator is already running
$adbPath = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$runningDevices = & $adbPath devices | Select-Object -Skip 1 | Where-Object { $_ -match "emulator" }

if ($runningDevices) {
    Write-Host "Currently Running Emulators:" -ForegroundColor Yellow
    foreach ($device in $runningDevices) {
        Write-Host "  - $device" -ForegroundColor White
    }
    Write-Host ""
    $response = Read-Host "An emulator is already running. Launch another one? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "Exiting..." -ForegroundColor Gray
        exit 0
    }
}

# Select emulator to launch
Write-Host ""
if ($avdList.Count -eq 0) {
    Write-Host "No emulators found. Please create one in Android Studio first." -ForegroundColor Red
    exit 1
} elseif ($avdList.Count -eq 1) {
    $selectedAvd = $avdList[0]
    Write-Host "Only one emulator found. Launching: $selectedAvd" -ForegroundColor Green
} else {
    Write-Host "Select an emulator to launch (1-$($avdList.Count)):" -ForegroundColor Cyan
    $choice = Read-Host "Enter number"
    try {
        $selectedIndex = [int]$choice - 1
        if ($selectedIndex -ge 0 -and $selectedIndex -lt $avdList.Count) {
            $selectedAvd = $avdList[$selectedIndex]
        } else {
            Write-Host "Invalid selection. Launching first emulator: $($avdList[0])" -ForegroundColor Yellow
            $selectedAvd = $avdList[0]
        }
    } catch {
        Write-Host "Invalid input. Launching first emulator: $($avdList[0])" -ForegroundColor Yellow
        $selectedAvd = $avdList[0]
    }
}

# Launch emulator
Write-Host ""
Write-Host "Launching emulator: $selectedAvd" -ForegroundColor Green
Write-Host "The emulator window will appear shortly. Please wait..." -ForegroundColor Yellow
Write-Host ""

# Launch in background (detached)
Start-Process -FilePath $emulatorPath -ArgumentList "-avd", $selectedAvd -WindowStyle Normal

Write-Host "Emulator is starting..." -ForegroundColor Green
Write-Host ""
Write-Host "Tips:" -ForegroundColor Cyan
Write-Host "  - The emulator window should appear on your screen" -ForegroundColor White
Write-Host "  - Check your taskbar if you don't see it" -ForegroundColor White
Write-Host "  - It may take 1-2 minutes to fully boot" -ForegroundColor White
Write-Host "  - Look for 'Android Emulator' in your taskbar" -ForegroundColor White
Write-Host ""

# Wait a bit and check connection
Start-Sleep -Seconds 5
$devices = & $adbPath devices
Write-Host "Connected devices:" -ForegroundColor Cyan
Write-Host $devices -ForegroundColor White

