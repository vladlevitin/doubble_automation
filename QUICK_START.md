# Quick Start Guide - Doubble Auto Swipe

## Fully Automated Swiping Script

This script automatically:
1. ✅ Checks all prerequisites (Python, Appium, Emulator)
2. ✅ Launches emulator if not running
3. ✅ Starts Appium server if not running
4. ✅ Opens Doubble app
5. ✅ Navigates to swipe screen
6. ✅ Continuously swipes profiles and presses like button
7. ✅ Handles pop-ups automatically

## How to Run

### Easiest Method (Recommended)
**Double-click:** `run_auto_swipe.bat`

### Alternative Methods
```powershell
# PowerShell
.\run_auto_swipe.bat

# Or directly
.\run_doubble_test.ps1
```

## What Happens

1. **Prerequisites Check**
   - Checks if Python is installed
   - Checks if Appium is installed
   - Checks if emulator is running (launches if not)
   - Checks if Appium server is running (starts if not)

2. **App Launch**
   - Opens Doubble app
   - Handles any initial pop-ups
   - Navigates to swipe screen if needed

3. **Continuous Swiping**
   - Clicks like button repeatedly
   - Handles pop-ups between actions
   - Swipes right (like gesture) if like button not found
   - Occasionally swipes left to pass (every 5 profiles)

## Stopping the Script

Press **Ctrl+C** to stop gracefully. The script will:
- Finish current action
- Clean up connections
- Close gracefully

## Requirements

- Python 3.11+
- Appium installed (`npm install -g appium`)
- Android emulator with Doubble app installed
- Dependencies: `pip install -r requirements.txt`

## Troubleshooting

### Emulator not starting?
- Make sure Android SDK is installed
- Check that you have at least one AVD created
- Try starting emulator manually first: `.\launch_emulator.ps1`

### Appium not starting?
- Make sure Node.js is installed
- Install Appium: `npm install -g appium`
- Try starting manually: `appium`

### App not opening?
- Make sure Doubble app is installed on the emulator
- Check that you're logged in (first time only)
- Verify package name in `config/settings.yaml`

## Logs

All actions are logged to console. Check the output for:
- Which pop-ups were detected and dismissed
- Like button clicks
- Swipe gestures
- Any errors or warnings

