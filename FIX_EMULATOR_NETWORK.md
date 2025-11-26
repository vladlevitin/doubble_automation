# Fix Emulator Network Connection

## Problem Found: No Internet Connection

Your emulator has **no internet connectivity**, which is why Play Store sign-in isn't working.

## Quick Fixes (Try in Order)

### Fix 1: Restart Emulator (Most Common Solution)

**This fixes network issues 80% of the time:**

1. **Close the emulator completely**
   - Click X on emulator window, OR
   - Run: `Get-Process | Where-Object {$_.ProcessName -like "*qemu*"} | Stop-Process`

2. **Wait 10 seconds**

3. **Launch emulator again**:
   ```powershell
   .\launch_emulator.ps1
   ```

4. **Wait for full boot** (2-3 minutes)

5. **Test network**:
   ```powershell
   & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell ping -c 3 8.8.8.8
   ```

---

### Fix 2: Restart ADB Server

**Sometimes ADB needs a restart:**

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" kill-server
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" start-server
```

Then test network again.

---

### Fix 3: Check Windows Network Settings

**Windows may be blocking emulator network:**

1. **Check Windows Firewall**:
   - Settings → Windows Security → Firewall
   - Make sure Android/emulator isn't blocked

2. **Check Network Adapter**:
   - Settings → Network & Internet → Status
   - Make sure your network is connected

3. **Restart Network Adapter** (if needed):
   - Run as Admin: `ipconfig /release` then `ipconfig /renew`

---

### Fix 4: Emulator Network Settings

**Check emulator network:**

1. On emulator, open **Settings**
2. Go to **Network & Internet**
3. Check **Wi-Fi** is connected
4. If not, try toggling Wi-Fi off/on

**Or via ADB**:
```powershell
# Check Wi-Fi status
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell dumpsys wifi | Select-String "Wi-Fi"
```

---

### Fix 5: Use Different Network Mode

**Launch emulator with specific network settings:**

```powershell
# Launch with network debugging
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Medium_Phone_API_36.1 -netdelay none -netspeed full
```

---

### Fix 6: Check DNS Settings

**Emulator may have DNS issues:**

1. On emulator: **Settings** → **Network & Internet** → **Wi-Fi**
2. Long-press connected network → **Modify network**
3. Change DNS to: `8.8.8.8` and `8.8.4.4` (Google DNS)

**Or via ADB**:
```powershell
# Set DNS
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell settings put global private_dns_mode hostname
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell settings put global private_dns_specifier 8.8.8.8
```

---

## Test Network Connection

**After trying fixes, test:**

```powershell
# Test ping
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell ping -c 3 8.8.8.8

# Should see: "3 packets transmitted, 3 received"
# If you see "100% packet loss" = still no internet
```

---

## Most Likely Solution

**90% of the time, restarting the emulator fixes it:**

1. ✅ **Close emulator completely**
2. ✅ **Wait 10 seconds**
3. ✅ **Launch again**: `.\launch_emulator.ps1`
4. ✅ **Wait for full boot** (2-3 minutes)
5. ✅ **Test network** - should work now
6. ✅ **Try Play Store sign-in** - should work

---

## Why This Happens

- **Network not initialized** during boot
- **ADB connection issues**
- **Windows firewall blocking**
- **Emulator network stack needs restart**

---

## After Network is Fixed

Once you have internet:

1. ✅ **Open Play Store**
2. ✅ **Wait for it to load** (may take 1-2 minutes first time)
3. ✅ **Sign in** - should work now!

**Or sign in through Settings** (more reliable):
1. Settings → Accounts → Add account → Google
2. Sign in there
3. Play Store will be signed in automatically

---

## Quick Diagnostic

```powershell
# Check emulator status
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices

# Check boot status
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell getprop sys.boot_completed

# Test network
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell ping -c 3 8.8.8.8

# Check Wi-Fi
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell dumpsys wifi | Select-String "mWifiInfo"
```

---

**Try restarting the emulator first - that fixes it most of the time!**

