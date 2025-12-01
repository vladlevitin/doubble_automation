"""
Script to find the correct main activity for Doubble app.
Uses ADB to query the app's launcher activity.
"""

import subprocess
import sys
from pathlib import Path

def find_main_activity(package_name: str = "dk.doubble.dating"):
    """Find the main launcher activity for an app."""
    
    # Find ADB
    adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
    
    if not adb_path.exists():
        # Try alternative location
        adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
        if not adb_path.exists():
            print(f"ERROR: ADB not found at {adb_path}")
            print("Please ensure Android SDK platform-tools is installed")
            return None
    
    print(f"Using ADB: {adb_path}")
    print(f"Finding main activity for package: {package_name}")
    print("=" * 60)
    
    # Method 1: Query launcher activity using dumpsys
    print("\nMethod 1: Querying launcher activity...")
    try:
        cmd = [str(adb_path), "shell", "dumpsys", "package", package_name, "|", "grep", "-A", "5", "android.intent.action.MAIN"]
        result = subprocess.run(
            f'{adb_path} shell "dumpsys package {package_name} | grep -A 5 android.intent.action.MAIN"',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 2: Use pm dump and parse
    print("\nMethod 2: Getting package info...")
    try:
        result = subprocess.run(
            [str(adb_path), "shell", "pm", "dump", package_name],
            capture_output=True,
            text=True
        )
        if result.stdout:
            # Look for activity filters with MAIN action
            lines = result.stdout.split('\n')
            in_activity = False
            current_activity = None
            for line in lines:
                if 'Activity #' in line or 'Activity{' in line:
                    in_activity = True
                    # Extract activity name
                    if 'Activity{' in line:
                        parts = line.split('Activity{')
                        if len(parts) > 1:
                            activity_part = parts[1].split()[0].rstrip('}')
                            current_activity = activity_part
                elif in_activity and 'android.intent.action.MAIN' in line:
                    if current_activity:
                        print(f"\n[FOUND] Main Activity: {current_activity}")
                        # Convert to relative format if needed
                        if current_activity.startswith(package_name):
                            relative = current_activity.replace(package_name + '.', '.')
                            print(f"[FOUND] Relative format: {relative}")
                            return relative
                        return current_activity
                elif in_activity and line.strip() == '':
                    in_activity = False
                    current_activity = None
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 3: Try to get current activity when app is running
    print("\nMethod 3: Checking current activity (if app is running)...")
    try:
        result = subprocess.run(
            [str(adb_path), "shell", "dumpsys", "window", "windows"],
            capture_output=True,
            text=True
        )
        if result.stdout and package_name in result.stdout:
            # Look for mCurrentFocus
            for line in result.stdout.split('\n'):
                if 'mCurrentFocus' in line and package_name in line:
                    print(f"Current activity: {line}")
                    # Extract activity name
                    if package_name in line:
                        parts = line.split(package_name)
                        if len(parts) > 1:
                            activity_part = parts[1].split()[0].rstrip('}').rstrip('/')
                            if activity_part.startswith('/'):
                                activity_part = activity_part[1:]
                            if activity_part.startswith('.'):
                                print(f"\n[FOUND] Main Activity: {activity_part}")
                                return activity_part
                            else:
                                full_activity = f"{package_name}.{activity_part}"
                                print(f"\n[FOUND] Main Activity: {full_activity}")
                                return f".{activity_part}"
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 4: Try common activity names
    print("\nMethod 4: Trying common activity names...")
    common_activities = [
        ".MainActivity",
        ".ui.MainActivity",
        ".MainActivityActivity",
        ".SplashActivity",
        ".LaunchActivity",
    ]
    
    for activity in common_activities:
        print(f"  Trying: {package_name}{activity}")
        try:
            result = subprocess.run(
                [str(adb_path), "shell", "am", "start", "-n", f"{package_name}/{activity}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"\n[SUCCESS] Activity works: {activity}")
                return activity
            elif "Error" not in result.stderr or "does not exist" not in result.stderr:
                print(f"  [MAYBE] Activity might exist: {activity}")
        except Exception as e:
            pass
    
    print("\n[ERROR] Could not find main activity automatically")
    print("Please check the app manually or use Appium Inspector")
    return None

if __name__ == "__main__":
    import os
    activity = find_main_activity()
    if activity:
        print("\n" + "=" * 60)
        print(f"Update config/settings.yaml with:")
        print(f"  app_activity: \"{activity}\"")
        print("=" * 60)
    else:
        print("\nCould not determine activity. Please:")
        print("1. Open the app manually on the emulator")
        print("2. Run: adb shell dumpsys window windows | findstr mCurrentFocus")
        print("3. Or use Appium Inspector to find the activity")

