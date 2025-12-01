# Complete automation script - Starts Appium and runs Doubble test
# This script handles everything in one go

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Doubble App Automation - Full Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  [OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Python not found! Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check if Appium is installed
Write-Host ""
Write-Host "[2/5] Checking Appium..." -ForegroundColor Yellow
try {
    $appiumVersion = appium --version 2>&1
    Write-Host "  [OK] Appium found: $appiumVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Appium not found! Please install: npm install -g appium" -ForegroundColor Red
    exit 1
}

# Check if emulator is running
Write-Host ""
Write-Host "[3/5] Checking emulator connection..." -ForegroundColor Yellow
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$emulatorPath = "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe"

if (Test-Path $adb) {
    $devices = & $adb devices 2>&1
    if ($devices -match "device$") {
        Write-Host "  [OK] Emulator is connected" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] No emulator connected" -ForegroundColor Yellow
        Write-Host "  -> Launching emulator automatically..." -ForegroundColor Cyan
        
        if (-not (Test-Path $emulatorPath)) {
            Write-Host "  [ERROR] Emulator executable not found!" -ForegroundColor Red
            Write-Host "    Please install Android SDK or start emulator manually" -ForegroundColor Yellow
            exit 1
        }
        
        # List available AVDs
        $avds = & $emulatorPath -list-avds 2>&1
        if ($avds.Count -eq 0) {
            Write-Host "  [ERROR] No emulators found! Please create one in Android Studio first." -ForegroundColor Red
            exit 1
        }
        
        # Find fastest emulator (prefer ones with snapshots for quick boot)
        Write-Host "  -> Checking available emulators..." -ForegroundColor Cyan
        $bestAvd = $null
        $bestAvdHasSnapshot = $false
        
        foreach ($avd in $avds) {
            # Check if this AVD has snapshots (quick boot capability)
            $avdPath = "$env:USERPROFILE\.android\avd\$avd.avd"
            $snapshotsPath = "$avdPath\snapshots"
            
            $hasSnapshot = $false
            if (Test-Path $snapshotsPath) {
                $snapshots = Get-ChildItem -Path $snapshotsPath -Directory -ErrorAction SilentlyContinue
                if ($snapshots.Count -gt 0) {
                    $hasSnapshot = $true
                }
            }
            
            # Prefer emulators with snapshots (faster boot)
            if ($hasSnapshot -and -not $bestAvdHasSnapshot) {
                $bestAvd = $avd
                $bestAvdHasSnapshot = $true
                Write-Host "    Found emulator with quick boot: $avd" -ForegroundColor Green
            } elseif (-not $bestAvdHasSnapshot -and -not $hasSnapshot) {
                # If no snapshot emulators found yet, keep first one
                if ($null -eq $bestAvd) {
                    $bestAvd = $avd
                }
            }
        }
        
        # If we found one with snapshot, use it; otherwise use first available
        if ($null -eq $bestAvd) {
            $bestAvd = $avds[0]
        }
        
        $avdName = $bestAvd
        if ($bestAvdHasSnapshot) {
            Write-Host "  -> Starting fastest emulator (with quick boot): $avdName" -ForegroundColor Cyan
            Write-Host "  -> Quick boot enabled - should start in 10-30 seconds!" -ForegroundColor Green
        } else {
            Write-Host "  -> Starting emulator: $avdName" -ForegroundColor Cyan
            Write-Host "  -> This may take 2-3 minutes for first boot..." -ForegroundColor Yellow
        }
        Write-Host "  -> This may take 2-3 minutes for first boot..." -ForegroundColor Yellow
        
        # Launch emulator in background (use quick boot if available)
        if ($bestAvdHasSnapshot) {
            # Use quick boot for faster startup
            Start-Process -FilePath $emulatorPath -ArgumentList "-avd", $avdName, "-no-snapshot-load" -WindowStyle Normal
            # Actually, let's use snapshot load for quick boot
            Start-Process -FilePath $emulatorPath -ArgumentList "-avd", $avdName -WindowStyle Normal
        } else {
            Start-Process -FilePath $emulatorPath -ArgumentList "-avd", $avdName -WindowStyle Normal
        }
        
        # Wait for emulator to boot (shorter wait if quick boot available)
        Write-Host "  -> Waiting for emulator to boot..." -ForegroundColor Cyan
        if ($bestAvdHasSnapshot) {
            $maxWait = 60  # 1 minute for quick boot
        } else {
            $maxWait = 300  # 5 minutes for cold boot
        }
        $waited = 0
        $emulatorReady = $false
        
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 5
            $waited += 5
            $devices = & $adb devices 2>&1
            
            if ($devices -match "device$") {
                # Check if boot is complete
                $bootStatus = & $adb shell getprop sys.boot_completed 2>&1
                if ($bootStatus -eq "1") {
                    $emulatorReady = $true
                    break
                }
            }
            
            if ($waited % 30 -eq 0) {
                Write-Host "    Still waiting... ($waited/$maxWait seconds)" -ForegroundColor Gray
            }
        }
        
        if ($emulatorReady) {
            Write-Host "  [OK] Emulator is ready!" -ForegroundColor Green
        } else {
            Write-Host "  [ERROR] Emulator failed to boot within $maxWait seconds" -ForegroundColor Red
            Write-Host "    Please start emulator manually and try again" -ForegroundColor Yellow
            exit 1
        }
    }
} else {
    Write-Host "  [ERROR] ADB not found! Please install Android SDK" -ForegroundColor Red
    exit 1
}

# Check if Appium server is running
Write-Host ""
Write-Host "[4/5] Checking Appium server..." -ForegroundColor Yellow
$ErrorActionPreference = 'SilentlyContinue'
$appiumRunning = Test-NetConnection -ComputerName localhost -Port 4723 -WarningAction SilentlyContinue -InformationLevel Quiet
$ErrorActionPreference = 'Continue'

if ($appiumRunning) {
    Write-Host "  [OK] Appium server is already running" -ForegroundColor Green
    $startAppium = $false
} else {
    Write-Host "  [WARN] Appium server is not running" -ForegroundColor Yellow
    Write-Host "  -> Starting Appium server in background..." -ForegroundColor Cyan
    
    # Start Appium in background
    $appiumJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        appium
    }
    
    Write-Host "  -> Waiting for Appium to start (this may take 10-20 seconds)..." -ForegroundColor Cyan
    
    # Wait for Appium to be ready (max 30 seconds)
    $maxWait = 30
    $waited = 0
    $appiumReady = $false
    
    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds 2
        $waited += 2
        $ErrorActionPreference = 'SilentlyContinue'
        $test = Test-NetConnection -ComputerName localhost -Port 4723 -WarningAction SilentlyContinue -InformationLevel Quiet
        $ErrorActionPreference = 'Continue'
        
        if ($test) {
            $appiumReady = $true
            break
        }
        Write-Host "    Still waiting... ($waited/$maxWait seconds)" -ForegroundColor Gray
    }
    
    if ($appiumReady) {
        Write-Host "  [OK] Appium server started successfully!" -ForegroundColor Green
        $startAppium = $true
    } else {
        Write-Host "  [ERROR] Appium server failed to start within $maxWait seconds" -ForegroundColor Red
        Write-Host "    Please start it manually: appium" -ForegroundColor Yellow
        Stop-Job $appiumJob -ErrorAction SilentlyContinue
        Remove-Job $appiumJob -ErrorAction SilentlyContinue
        exit 1
    }
}

# Run the test
Write-Host ""
Write-Host "[5/5] Running Doubble app automation..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The script will:" -ForegroundColor Cyan
Write-Host "  - Launch Doubble app" -ForegroundColor White
Write-Host "  - Navigate to swipe screen" -ForegroundColor White
Write-Host "  - Continuously swipe profiles and press like button" -ForegroundColor White
Write-Host "  - Handle pop-ups automatically" -ForegroundColor White
Write-Host "  - Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

try {
    # Run the automated Python script
    python auto_doubble_swipe.py
    $testExitCode = $LASTEXITCODE
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    
    if ($testExitCode -eq 0) {
        Write-Host "  [OK] Test completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Test completed with errors (exit code: $testExitCode)" -ForegroundColor Red
    }
    
} catch {
    Write-Host ""
    Write-Host "  [ERROR] Error running test: $_" -ForegroundColor Red
    $testExitCode = 1
}

# Cleanup
Write-Host ""
if ($startAppium) {
    Write-Host "Cleaning up Appium server..." -ForegroundColor Yellow
    Stop-Job $appiumJob -ErrorAction SilentlyContinue
    Remove-Job $appiumJob -ErrorAction SilentlyContinue
    Write-Host "  [OK] Cleanup complete" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path variable:testExitCode)) {
    $testExitCode = 0
}

exit $testExitCode
