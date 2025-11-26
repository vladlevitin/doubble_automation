# Quick Start: Running Android Emulator

## Method 1: Using the PowerShell Script (Easiest)

I've created a helper script for you. Just run:

```powershell
.\launch_emulator.ps1
```

This script will:
- Show you all available emulators
- Let you select which one to launch
- Launch it for you
- Show you connection status

## Method 2: Using Command Line Directly

### List Available Emulators
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -list-avds
```

### Launch a Specific Emulator
```powershell
# Launch Pixel_9_Pro
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Pixel_9_Pro

# Or launch Medium_Phone_API_36.1
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Medium_Phone_API_36.1
```

### Check if Emulator is Running
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
```

## Method 3: Using Android Studio

1. Open **Android Studio**
2. Go to **Tools** → **Device Manager** (or click the device manager icon in the toolbar)
3. Find your emulator in the list
4. Click the **▶️ Play button** next to the emulator name
5. The emulator window will open

## Finding the Emulator Window

### Where to Look:

1. **On Your Screen**
   - The emulator appears as a separate window showing an Android phone/tablet
   - It should automatically appear when launched
   - Look for a window titled "Android Emulator" or similar

2. **In Taskbar**
   - Check your Windows taskbar
   - Look for "Android Emulator" or "qemu-system" icon
   - Click it to bring the window to front

3. **Using Alt+Tab**
   - Press `Alt + Tab` to cycle through open windows
   - Look for the emulator window

4. **Check All Monitors**
   - If you have multiple monitors, check all of them
   - The emulator might open on a different screen

5. **Minimized Window**
   - Check if it's minimized in the taskbar
   - Right-click the taskbar icon and select "Restore"

### If You Can't Find It:

1. **Check if it's actually running:**
   ```powershell
   & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices
   ```
   - If you see `emulator-5554 device`, it's running
   - If you see `emulator-5554 offline`, wait a bit longer (it's still booting)

2. **Kill and restart:**
   ```powershell
   # Kill all emulator processes
   Get-Process | Where-Object {$_.ProcessName -like "*emulator*" -or $_.ProcessName -like "*qemu*"} | Stop-Process -Force
   
   # Then launch again
   & "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Pixel_9_Pro
   ```

3. **Launch with visible window:**
   ```powershell
   # Launch and keep window visible
   & "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Pixel_9_Pro -window
   ```

## Your Available Emulators

Based on your system, you have:
- `Medium_Phone_API_36.1`
- `Pixel_9_Pro`

## Quick Commands Reference

```powershell
# List emulators
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -list-avds

# Launch emulator (replace with your AVD name)
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Pixel_9_Pro

# Check running devices
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices

# Take screenshot of emulator
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell screencap -p /sdcard/screen.png
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" pull /sdcard/screen.png
```

## Troubleshooting

### Emulator Won't Appear
- **Wait 1-2 minutes** - First boot takes time
- **Check Task Manager** - Look for "qemu-system" or "emulator" processes
- **Check all monitors** - It might be on another screen
- **Restart the emulator** - Close and launch again

### Emulator is Slow
- **Increase RAM** in AVD settings (Device Manager → Edit → Show Advanced Settings)
- **Close other applications**
- **Enable hardware acceleration** in BIOS (Intel VT-x or AMD-V)

### Can't Connect via ADB
- **Wait for full boot** - Emulator must be fully started
- **Check connection**: `adb devices` should show `device` (not `offline`)
- **Restart ADB server**: `adb kill-server` then `adb start-server`

## Next Steps

Once the emulator is running and visible:
1. ✅ Sign in with Google account (open Play Store)
2. ✅ Install your app
3. ✅ Get package name: `adb shell dumpsys window windows | Select-String "mCurrentFocus"`
4. ✅ Update `config/settings.yaml` with package/activity
5. ✅ Run your automation: `python main.py`

