# Android Emulator Setup Guide - Google Login & App Installation

This guide will help you launch an Android emulator with Google Play Services, sign in with your Google account, and install your app.

## Prerequisites

- **Android Studio** must be installed
- **Android SDK** should be set up (comes with Android Studio)

## Step 1: Create an Android Virtual Device (AVD) with Google Play

### Option A: Using Android Studio (Recommended)

1. **Open Android Studio**
   - Launch Android Studio
   - If you see a welcome screen, click "More Actions" → "Virtual Device Manager"
   - Or go to: **Tools** → **Device Manager**

2. **Create a New Virtual Device**
   - Click **"Create Device"** button
   - Select a device definition (e.g., "Pixel 6" or "Pixel 7")
   - Click **"Next"**

3. **Select System Image with Google Play**
   - **IMPORTANT**: Choose a system image that has the **Play Store icon** (🛒) next to it
   - Look for images labeled:
     - "Release Name" (e.g., "Tiramisu", "UpsideDownCake")
     - **"Google Play"** column should show **"Yes"**
   - Recommended: **Android 13 (Tiramisu)** or **Android 14 (UpsideDownCake)**
   - Click **"Download"** if the image isn't installed yet
   - Click **"Next"**

4. **Configure AVD**
   - Name your device (e.g., "Pixel_6_API_33")
   - Review settings (you can change RAM, storage, etc.)
   - Click **"Finish"**

### Option B: Using Command Line

If you prefer command line, you can use `avdmanager`:

```bash
# List available system images with Google Play
sdkmanager --list | findstr "google_apis_playstore"

# Create AVD (example - adjust version as needed)
avdmanager create avd -n Pixel_6_API_33 -k "system-images;android-33;google_apis;x86_64" -d "pixel_6"
```

## Step 2: Launch the Emulator

### Using Android Studio:
1. In **Device Manager**, find your newly created device
2. Click the **▶️ Play button** next to your device
3. Wait for the emulator to boot (may take 1-2 minutes)

### Using Command Line:
```bash
# List available AVDs
emulator -list-avds

# Launch the emulator (replace with your AVD name)
emulator -avd Pixel_6_API_33
```

## Step 3: Set Up Google Account

1. **Wait for Emulator to Fully Boot**
   - The emulator will show the Android home screen
   - Wait until you see the Google Play Store icon

2. **Open Google Play Store**
   - Tap the **Play Store** icon on the home screen
   - If you see a setup wizard, follow it

3. **Sign In with Google Account**
   - Tap **"Sign in"** or the profile icon
   - Enter your Google account email
   - Enter your password
   - Complete 2-factor authentication if prompted
   - Accept terms and conditions

4. **Verify Google Services**
   - Open **Settings** → **Accounts**
   - You should see your Google account listed
   - This confirms Google Play Services is working

## Step 4: Install Your App

### Option A: Install from Google Play Store

1. **Open Google Play Store**
2. **Search for your app**
   - Use the search bar at the top
   - Type your app name
3. **Install the app**
   - Tap **"Install"** button
   - Wait for installation to complete
   - Tap **"Open"** to launch

### Option B: Install APK File

If you have an APK file:

1. **Transfer APK to Emulator**
   ```bash
   # Using ADB (replace with your APK path)
   adb install "C:\path\to\your\app.apk"
   ```

2. **Or Drag and Drop**
   - Simply drag the APK file from Windows Explorer
   - Drop it onto the emulator window
   - Follow the installation prompts

### Option C: Install via ADB (Alternative)

```bash
# Check if emulator is connected
adb devices

# Install APK
adb install path\to\your\app.apk

# If app is already installed and you want to reinstall
adb install -r path\to\your\app.apk
```

## Step 5: Verify Installation

1. **Check if app is installed**
   ```bash
   # List all installed packages
   adb shell pm list packages | findstr "your.app.package"
   
   # Or find the package name
   adb shell pm list packages | findstr "appname"
   ```

2. **Launch the app manually**
   - Find the app icon on the emulator home screen
   - Tap to open it
   - Complete any initial setup or login

## Step 6: Get App Package Name and Activity

After installing your app, you need to find its package name and main activity for the automation framework:

### Method 1: Using ADB (While App is Running)

1. **Launch your app** on the emulator
2. **Run this command**:
   ```bash
   adb shell dumpsys window windows | findstr "mCurrentFocus"
   ```
3. **Output example**:
   ```
   mCurrentFocus=Window{...} com.example.myapp/.ui.MainActivity
   ```
   - Package: `com.example.myapp`
   - Activity: `.ui.MainActivity`

### Method 2: Using ADB Package Manager

```bash
# List all packages and find yours
adb shell pm list packages | findstr "your.app.keyword"

# Get main activity for a package
adb shell pm dump com.example.myapp | findstr "android.intent.action.MAIN" -A 5
```

### Method 3: Using Appium Inspector

1. Start Appium server: `appium`
2. Open Appium Inspector
3. Connect to your app
4. The package and activity will be shown in the inspector

## Step 7: Update Framework Configuration

Once you have the package name and activity, update `config/settings.yaml`:

```yaml
android:
  app_package: "com.example.myapp"  # Your actual package name
  app_activity: ".ui.MainActivity"   # Your actual main activity
```

## Troubleshooting

### Emulator Won't Start
- **Check if virtualization is enabled** in BIOS (Intel VT-x or AMD-V)
- **Close other emulators** that might be running
- **Increase RAM allocation** in AVD settings (recommended: 4GB+)

### Google Play Store Not Available
- **Make sure you selected a system image with Google Play** (has 🛒 icon)
- **Recreate the AVD** with a Google Play image
- Some system images don't include Google Play Services

### Can't Sign In to Google
- **Check internet connection** on emulator
- **Try signing in through Settings** → Accounts → Add Account
- **Clear Play Store cache**: Settings → Apps → Google Play Store → Clear Cache

### App Won't Install
- **Check if app is compatible** with your Android version
- **Enable "Install from Unknown Sources"** if installing APK:
  - Settings → Security → Unknown Sources (enable)
- **Check ADB connection**: `adb devices`

### Can't Find Package Name
- **Make sure app is running** when using `dumpsys window`
- **Try using Appium Inspector** for easier discovery
- **Check app's AndroidManifest.xml** if you have access to source code

## Quick Reference Commands

```bash
# List all AVDs
emulator -list-avds

# Launch emulator
emulator -avd <avd_name>

# Check connected devices
adb devices

# Install APK
adb install path\to\app.apk

# Get current app package/activity
adb shell dumpsys window windows | findstr "mCurrentFocus"

# List installed packages
adb shell pm list packages

# Uninstall app
adb uninstall com.example.myapp

# Take screenshot
adb shell screencap -p /sdcard/screenshot.png
adb pull /sdcard/screenshot.png
```

## Next Steps

After setting up the emulator and installing your app:

1. ✅ Launch emulator with Google Play
2. ✅ Sign in with Google account
3. ✅ Install your app
4. ✅ Get package name and activity
5. ✅ Update `config/settings.yaml`
6. ✅ Log in to your app manually (first time)
7. ✅ Run automation tests: `python main.py`

---

**Note**: The first time you launch an emulator, it may take several minutes to boot. Subsequent launches will be faster.

