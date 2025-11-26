# Google Play Store Sign-In Troubleshooting

## Common Issues & Solutions

### 1. ⏳ Wait for Full Boot (Most Common)

**Problem**: Play Store won't work until emulator is fully booted.

**Solution**:
- Wait for home screen to appear
- Wait 1-2 minutes AFTER home screen appears
- Let Google Play Services fully initialize
- Try opening Play Store again

**Check if ready**:
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell getprop sys.boot_completed
```
Should return `1` when ready.

---

### 2. 🌐 Network Connectivity Issues

**Problem**: Emulator can't connect to internet.

**Check connectivity**:
```powershell
# Test internet connection
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell ping -c 3 8.8.8.8
```

**Solutions**:
- **Restart emulator** - Network may not be initialized
- **Check Windows firewall** - May be blocking emulator
- **Check network settings** in emulator:
  - Settings → Network & Internet → Check Wi-Fi is connected
- **Restart ADB**:
  ```powershell
  & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" kill-server
  & "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" start-server
  ```

---

### 3. 🔄 Google Play Services Not Updated

**Problem**: Play Store needs updated Google Play Services.

**Solution**:
1. Open **Settings** on emulator
2. Go to **Apps** → **Google Play Services**
3. Check if update is available
4. Update if needed
5. Restart emulator

**Or update via ADB**:
```powershell
# Check Play Services version
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell dumpsys package com.google.android.gms | Select-String "versionName"
```

---

### 4. 🧹 Clear Play Store Cache

**Problem**: Corrupted cache preventing sign-in.

**Solution**:
1. Open **Settings** on emulator
2. Go to **Apps** → **Google Play Store**
3. Tap **Storage**
4. Tap **Clear Cache**
5. Tap **Clear Data** (if needed)
6. Restart Play Store

**Or via ADB**:
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell pm clear com.android.vending
```

---

### 5. 🔐 Sign In Through Settings Instead

**Alternative method** (often more reliable):

1. Open **Settings** on emulator
2. Go to **Accounts** (or **Users & accounts**)
3. Tap **Add account**
4. Select **Google**
5. Sign in with your Google account
6. Then open Play Store - it should be signed in

---

### 6. ⚠️ Use System Image with Google Play

**Problem**: Emulator doesn't have Google Play Services.

**Check**:
- Make sure you're using a system image with **Google Play** (🛒 icon)
- Not just "Google APIs" - needs "Google Play"

**Solution**:
- Create new AVD with Google Play system image
- Or reinstall Play Store if missing

---

### 7. 🕐 Wait Longer (First Time Setup)

**Problem**: First-time Play Store setup takes time.

**What to expect**:
- Play Store may take 2-5 minutes to fully load first time
- Sign-in process may take 1-2 minutes
- Be patient - it's normal!

**Steps**:
1. Open Play Store
2. Wait for it to fully load (may show "Checking info...")
3. Tap **Sign in**
4. Wait for sign-in screen to appear
5. Enter credentials
6. Wait for authentication (may take 1-2 minutes)

---

### 8. 🔄 Restart Play Store

**Quick fix**:
1. Close Play Store completely
2. Wait 10 seconds
3. Open Play Store again
4. Try sign-in

**Force stop via ADB**:
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell am force-stop com.android.vending
```

---

### 9. 🌍 Check Date & Time

**Problem**: Incorrect date/time can break authentication.

**Solution**:
1. Open **Settings** → **System** → **Date & time**
2. Enable **Automatic date & time**
3. Or set manually to correct time

**Check via ADB**:
```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell date
```

---

### 10. 🔒 Two-Factor Authentication Issues

**Problem**: 2FA may not work well in emulator.

**Solutions**:
- Use **App Password** instead of regular password
- Or temporarily disable 2FA for testing
- Or use backup codes

---

## Step-by-Step Troubleshooting

### Step 1: Verify Emulator is Ready
```powershell
# Check boot status
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell getprop sys.boot_completed

# Should return: 1
```

### Step 2: Check Network
```powershell
# Test internet
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell ping -c 3 8.8.8.8
```

### Step 3: Check Play Store
```powershell
# Check if Play Store is installed
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell pm list packages | Select-String "vending"
```

### Step 4: Clear Cache
```powershell
# Clear Play Store cache
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell pm clear com.android.vending
```

### Step 5: Restart Play Store
```powershell
# Force stop and restart
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell am force-stop com.android.vending
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell am start -n com.android.vending/.AssetBrowserActivity
```

---

## Recommended Approach

### Method 1: Sign In Through Settings (Most Reliable)
1. ✅ Wait for emulator to fully boot
2. ✅ Open **Settings** → **Accounts**
3. ✅ Add Google account
4. ✅ Sign in
5. ✅ Open Play Store (should be signed in)

### Method 2: Direct Play Store Sign-In
1. ✅ Wait 2-3 minutes after boot
2. ✅ Open Play Store
3. ✅ Wait for it to fully load
4. ✅ Tap Sign in
5. ✅ Enter credentials
6. ✅ Be patient (may take 1-2 minutes)

---

## Quick Diagnostic Commands

```powershell
# Check emulator status
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" devices

# Check boot status
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell getprop sys.boot_completed

# Test internet
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell ping -c 3 8.8.8.8

# Check Play Store
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell pm list packages | Select-String "vending"

# Clear Play Store cache
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell pm clear com.android.vending

# Restart Play Store
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" shell am force-stop com.android.vending
```

---

## Most Common Solution

**90% of the time, it's one of these:**

1. ⏳ **Not waiting long enough** - Play Store needs 2-3 minutes after boot
2. 🌐 **Network not ready** - Wait for network to initialize
3. 🔄 **Sign in through Settings** - More reliable than Play Store directly

**Try this first:**
1. Wait 2-3 minutes after emulator boots
2. Open **Settings** → **Accounts** → **Add account** → **Google**
3. Sign in there
4. Then open Play Store

---

## Still Not Working?

If none of the above works:
1. **Restart the emulator** completely
2. **Wait 3-5 minutes** after restart
3. **Try signing in through Settings** (not Play Store)
4. **Check Windows firewall** isn't blocking emulator
5. **Try a different network** (if possible)

---

**Remember**: First-time Play Store setup is always slow. Be patient - it can take 3-5 minutes total!

