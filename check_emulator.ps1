# Quick Emulator Status Checker
# Run this script to check if your emulator is ready

$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"

Write-Host "=== Emulator Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Check connected devices
Write-Host "Connected Devices:" -ForegroundColor Yellow
$devices = & $adb devices
Write-Host $devices
Write-Host ""

# Check boot status
Write-Host "Boot Status:" -ForegroundColor Yellow
try {
    $bootStatus = & $adb shell getprop sys.boot_completed 2>$null
    if ($bootStatus -eq "1") {
        Write-Host "✅ Emulator is FULLY BOOTED and READY!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Open Google Play Store on the emulator" -ForegroundColor White
        Write-Host "  2. Sign in with your Google account" -ForegroundColor White
        Write-Host "  3. Install your app" -ForegroundColor White
    } else {
        Write-Host "⏳ Emulator is still booting..." -ForegroundColor Yellow
        Write-Host "   Please wait for the home screen to appear." -ForegroundColor Yellow
        Write-Host "   This can take 1-3 minutes, especially on first boot." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⏳ Emulator is still initializing..." -ForegroundColor Yellow
    Write-Host "   Status: OFFLINE (this is normal during boot)" -ForegroundColor Yellow
    Write-Host "   Wait for the Android home screen to appear." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Tip: Run this script again in 30 seconds to check status." -ForegroundColor Gray
Write-Host "     Command: .\check_emulator.ps1" -ForegroundColor Gray

