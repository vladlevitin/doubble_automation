# How to Speed Up Android Emulator

## Why Is It Slow?

### Common Reasons:
1. **First boot is always slowest** - Can take 3-5 minutes
2. **Not enough RAM allocated** - Default might be too low
3. **Hardware acceleration not enabled** - Using software rendering
4. **Too many apps running** - Competing for resources
5. **Multiple emulators running** - Each uses significant resources
6. **Slow disk** - HDD is much slower than SSD
7. **CPU limitations** - Emulator is CPU-intensive

## Quick Fixes (Try These First)

### 1. Increase RAM Allocation
**This is the #1 speed improvement!**

1. Open **Android Studio**
2. Go to **Tools** → **Device Manager**
3. Find your emulator → Click **Edit** (pencil icon)
4. Click **Show Advanced Settings**
5. Under **Memory and Storage**:
   - **RAM**: Increase to **4096 MB** or **6144 MB** (if you have 16GB+ system RAM)
   - **VM heap**: Set to **512 MB**
6. Click **Finish**
7. **Restart the emulator**

### 2. Enable Hardware Acceleration
**Check if enabled:**
```powershell
# Check if hardware acceleration is available
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -accel-check
```

**If not enabled, enable it:**
- **Intel CPUs**: Enable **Intel VT-x** in BIOS
- **AMD CPUs**: Enable **AMD-V** in BIOS
- **Windows**: Enable **Windows Hypervisor Platform (WHPX)**

### 3. Close Other Applications
- Close unnecessary browser tabs
- Close other heavy applications
- Close other emulators if running multiple
- Free up system resources

### 4. Use Quick Boot (Snapshots)
**After first boot, use snapshots for faster startup:**

1. When emulator is running, click **...** (three dots) menu
2. Go to **Snapshots**
3. Click **Take Snapshot** (or it auto-saves)
4. Next time, select **Quick Boot** when launching

### 5. Reduce Emulator Resolution
**Lower resolution = faster performance:**

1. **Device Manager** → **Edit** your emulator
2. Under **Graphics**:
   - Change from **Automatic** to **Hardware - GLES 2.0**
   - Or reduce resolution if possible

## Advanced Optimizations

### 1. Use x86_64 System Images
**Make sure you're using 64-bit images:**
- ✅ `x86_64` (64-bit) - **Faster**
- ❌ `x86` (32-bit) - Slower
- ❌ `arm` - Very slow (only use if necessary)

### 2. Adjust CPU Cores
**In AVD settings:**
- **CPU cores**: Set to **2-4 cores** (don't use all cores)
- Too many cores can actually slow it down

### 3. Use SSD Instead of HDD
**If possible, move AVD to SSD:**
- Default location: `C:\Users\<YourName>\.android\avd\`
- Move to SSD if you have one
- Or use faster storage

### 4. Disable Unnecessary Features
**In emulator settings, disable:**
- Camera (if not needed)
- Microphone (if not needed)
- Location services (if not needed)
- NFC (if not needed)

## Performance Comparison

### Typical Boot Times:
- **First boot (cold)**: 3-5 minutes
- **Subsequent boots (warm)**: 1-2 minutes
- **Quick boot (snapshot)**: 10-30 seconds ⚡

### After Optimizations:
- **First boot**: 2-3 minutes
- **Subsequent boots**: 30-60 seconds
- **Quick boot**: 5-15 seconds ⚡⚡

## Check Current Performance

### See what's using resources:
```powershell
# Check emulator processes
Get-Process | Where-Object {$_.ProcessName -like "*qemu*" -or $_.ProcessName -like "*emulator*"} | Select-Object ProcessName, @{Name="CPU%";Expression={$_.CPU}}, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet64/1MB,2)}}
```

### Check system resources:
```powershell
# Check available RAM
Get-CimInstance Win32_OperatingSystem | Select-Object @{Name="TotalRAM(GB)";Expression={[math]::Round($_.TotalVisibleMemorySize/1MB/1024,2)}}, @{Name="FreeRAM(GB)";Expression={[math]::Round($_.FreePhysicalMemory/1MB/1024,2)}}
```

## Recommended Settings

### For 8GB System RAM:
- Emulator RAM: **2048 MB**
- VM heap: **256 MB**

### For 16GB System RAM:
- Emulator RAM: **4096 MB** ⭐ **Recommended**
- VM heap: **512 MB**

### For 32GB+ System RAM:
- Emulator RAM: **6144 MB** or **8192 MB**
- VM heap: **512 MB**

## Quick Commands

```powershell
# Check hardware acceleration
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -accel-check

# Launch with specific RAM (temporary)
& "$env:LOCALAPPDATA\Android\Sdk\emulator\emulator.exe" -avd Medium_Phone_API_36.1 -memory 4096

# Check running processes
Get-Process | Where-Object {$_.ProcessName -like "*qemu*"} | Format-Table
```

## Most Important Tips

1. ⭐ **Increase RAM to 4GB** - Biggest impact
2. ⭐ **Use Quick Boot** after first boot
3. ⭐ **Close other applications**
4. ⭐ **Enable hardware acceleration**
5. ⭐ **Use x86_64 system images**

## After First Boot

**The first boot is ALWAYS the slowest!**
- Once booted, use **Quick Boot** for future launches
- Quick Boot uses snapshots and starts in 10-30 seconds
- Much faster than cold boot every time

---

**Remember**: First boot takes 3-5 minutes. After that, use Quick Boot for much faster startup!

