# Script to find the correct main activity for Doubble app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Finding Doubble App Activity" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find ADB
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
if (-not (Test-Path $adb)) {
    $adb = "C:\LDPlayer\LDPlayer9\adb.exe"
}

if (-not (Test-Path $adb)) {
    Write-Host "[ERROR] ADB not found!" -ForegroundColor Red
    Write-Host "Please ensure Android SDK is installed" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Using ADB: $adb" -ForegroundColor Green
Write-Host ""

# Check if emulator is connected
Write-Host "Checking emulator connection..." -ForegroundColor Yellow
$devices = & $adb devices 2>&1
if ($devices -notmatch "device$") {
    Write-Host "[ERROR] No emulator connected!" -ForegroundColor Red
    Write-Host "Please start your emulator first" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Emulator connected" -ForegroundColor Green
Write-Host ""

# Method 1: Check if app is currently running
Write-Host "Method 1: Checking if Doubble app is running..." -ForegroundColor Cyan
$currentWindow = & $adb shell "dumpsys window windows" 2>&1 | Select-String "mCurrentFocus"
if ($currentWindow -match "dk\.doubble\.dating") {
    Write-Host "[FOUND] App is running!" -ForegroundColor Green
    Write-Host $currentWindow -ForegroundColor White
    
    # Extract activity
    if ($currentWindow -match "dk\.doubble\.dating[/.]([^\s}]+)") {
        $fullActivity = $matches[0]
        $activity = $matches[1]
        
        Write-Host ""
        Write-Host "[SUCCESS] Activity found:" -ForegroundColor Green
        Write-Host "  Full: $fullActivity" -ForegroundColor White
        
        # Convert to relative format
        if ($activity -match "^dk\.doubble\.dating\.(.+)") {
            $relativeActivity = "." + $matches[1]
        } elseif ($activity -match "^\.(.+)") {
            $relativeActivity = $activity
        } else {
            $relativeActivity = ".$activity"
        }
        
        Write-Host "  Relative: $relativeActivity" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Update config/settings.yaml with:" -ForegroundColor Cyan
        Write-Host "  app_activity: `"$relativeActivity`"" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "[INFO] App is not currently running" -ForegroundColor Yellow
}

Write-Host ""

# Method 2: Query package info
Write-Host "Method 2: Querying package info..." -ForegroundColor Cyan
$packageInfo = & $adb shell "pm dump dk.doubble.dating" 2>&1

if ($packageInfo) {
    # Look for MAIN action activities
    $mainActivities = $packageInfo | Select-String -Pattern "android.intent.action.MAIN" -Context 0,10
    
    if ($mainActivities) {
        Write-Host "[FOUND] Main activities:" -ForegroundColor Green
        foreach ($line in $mainActivities) {
            Write-Host $line -ForegroundColor White
            
            # Try to extract activity name
            if ($line -match "Activity #\d+ ([^\s]+)") {
                $activity = $matches[1]
                Write-Host "  -> Activity: $activity" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "[INFO] Could not find MAIN action in package dump" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] Could not query package info" -ForegroundColor Red
}

Write-Host ""

# Method 3: Try to launch app and check activity
Write-Host "Method 3: Instructions for manual check..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Please do the following:" -ForegroundColor Yellow
Write-Host "1. Open Doubble app manually on the emulator" -ForegroundColor White
Write-Host "2. Then run this command:" -ForegroundColor White
Write-Host "   $adb shell `"dumpsys window windows | grep mCurrentFocus`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or run this script again after opening the app." -ForegroundColor Yellow
Write-Host ""
Write-Host "Alternative: Use Appium Inspector to find the activity" -ForegroundColor Yellow

