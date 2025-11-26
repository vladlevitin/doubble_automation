# Emulator Boot Status Guide

## What's Happening

Your emulator (`Pixel_9_Pro`) is currently booting. This is **completely normal** and can take 1-3 minutes, especially:
- First boot after creation
- After a system restart
- If your computer is under load

## Boot Process Stages

1. ✅ **Hardware initialization** - GPU, memory, network (you're past this)
2. ✅ **System image loading** - Android OS starting up
3. ⏳ **Android boot animation** - The "Android" logo spinning
4. ⏳ **System services starting** - Google Play Services, etc.
5. ⏳ **Home screen appears** - You'll see the Android home screen

## How to Check if It's Ready

### Method 1: Watch the Emulator Window
- Look for the Android boot animation (spinning "Android" logo)
- Wait until you see the home screen with app icons
- The screen should be fully interactive (not frozen)

### Method 2: Check ADB Connection
Run this command in PowerShell:
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
```

**Status meanings:**
- `emulator-5554    device` ✅ **Ready!** - Fully booted and ready to use
- `emulator-5554    offline` ⏳ **Still booting** - Wait a bit longer
- `emulator-5554    unauthorized` ⚠️ **Needs authorization** - Check emulator window for popup

### Method 3: Check Boot Complete
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell getprop sys.boot_completed
```

**Output:**
- `1` ✅ **Booted!** - System is ready
- `0` or nothing ⏳ **Still booting** - Wait more

## What to Expect

### Normal Boot Time:
- **First boot**: 2-5 minutes
- **Subsequent boots**: 1-2 minutes
- **Cold boot** (after restart): 2-3 minutes

### Visual Indicators:
1. **Boot animation** - Spinning Android logo
2. **"Optimizing apps"** - May appear on first boot
3. **Home screen** - Grid of app icons appears
4. **Status bar** - Shows battery, time, signal at top

## Once It's Ready

### 1. Sign In with Google
- Open **Google Play Store** app
- Tap **"Sign in"**
- Enter your Google account credentials
- Complete any 2FA if prompted

### 2. Install Your App
- Search for your app in Play Store, OR
- Install via ADB: `adb install path\to\app.apk`

### 3. Get App Package Info
After launching your app:
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell dumpsys window windows | Select-String "mCurrentFocus"
```

### 4. Update Configuration
Edit `config/settings.yaml` with your app's package name and activity.

## Troubleshooting

### Emulator Stuck on Boot Animation
- **Wait 5 minutes** - First boot can be slow
- **Check system resources** - Close other heavy applications
- **Restart emulator** - Close and launch again

### Emulator Shows "Offline"
- **Wait longer** - System is still initializing
- **Check emulator window** - Make sure it's not minimized
- **Restart ADB**: 
  ```powershell
  & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" kill-server
  & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" start-server
  ```

### Emulator is Very Slow
- **Increase RAM** in AVD settings (Device Manager → Edit → Show Advanced)
- **Enable hardware acceleration** in BIOS (Intel VT-x or AMD-V)
- **Close other applications** to free up resources

### Can't See Emulator Window
- **Check taskbar** - Look for "Android Emulator" icon
- **Press Alt+Tab** - Cycle through windows
- **Check all monitors** - May be on another screen

## Quick Status Check Script

Save this as `check_emulator.ps1`:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
Write-Host "Checking emulator status..." -ForegroundColor Cyan

$devices = & $adb devices
Write-Host $devices

$bootStatus = & $adb shell getprop sys.boot_completed 2>$null
if ($bootStatus -eq "1") {
    Write-Host "`n✅ Emulator is READY!" -ForegroundColor Green
} else {
    Write-Host "`n⏳ Emulator is still booting..." -ForegroundColor Yellow
    Write-Host "Please wait for the home screen to appear." -ForegroundColor Yellow
}
```

## Next Steps After Boot

1. ✅ Wait for home screen to appear
2. ✅ Open Google Play Store
3. ✅ Sign in with Google account
4. ✅ Install your app
5. ✅ Get package name and activity
6. ✅ Update `config/settings.yaml`
7. ✅ Run automation: `python main.py`

---

**Patience is key!** The first boot is always the slowest. Once it's running, subsequent boots will be much faster.

