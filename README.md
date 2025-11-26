# Android Automation Framework

A production-quality, minimal Android test automation framework built with Python and Appium.

## Features

- ✅ Launch Android apps in emulator or attach to running devices
- ✅ Reliable UI element location using multiple strategies
- ✅ Basic interactions: taps, swipes, text entry, navigation
- ✅ Structured logging with file and console output
- ✅ Page Object Model pattern for maintainability
- ✅ Preserves login state between test runs
- ✅ Easy to extend with new test cases

## Architecture

### Config Layer
YAML-based configuration for Appium capabilities, device settings, and app identifiers.

### Driver Layer
Factory pattern for creating and managing Appium WebDriver instances with connection to Android emulator/device via ADB.

### Page Object Layer
Base page class with common UI interaction methods. Specific page classes inherit from base and encapsulate page-specific logic.

### Test Layer
Pytest-based test cases that use page objects to perform user flows and validations.

### Logging
Structured logging with file and console handlers. All actions, errors, and test results are logged with timestamps.

## Prerequisites

### 1. Install Python
- Python 3.11 or higher
- Add Python to PATH

### 2. Install Android Development Tools
- **Android Studio**: Download from [developer.android.com](https://developer.android.com/studio)
- **Android SDK**: Installed with Android Studio
- **ADB (Android Debug Bridge)**: Included with Android SDK
- Add Android SDK platform-tools to PATH:
  ```
  C:\Users\<YourUsername>\AppData\Local\Android\Sdk\platform-tools
  ```

### 3. Install Node.js
- Download from [nodejs.org](https://nodejs.org/)
- Required for Appium server

### 4. Install Appium
```bash
npm install -g appium
npm install -g @appium/uiautomator2-driver
```

### 5. Install Appium Inspector (Optional but Recommended)
- Download from [Appium Inspector releases](https://github.com/appium/appium-inspector/releases)
- Useful for inspecting UI elements and generating locators

## Setup

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your App

Edit `config/settings.yaml`:

```yaml
android:
  platform_version: "13.0"  # Match your emulator version
  app_package: "com.example.myapp"  # Your app's package name
  app_activity: ".ui.MainActivity"  # Your app's main activity
```

**How to find package name and activity:**
- Use Appium Inspector to inspect your app
- Or use ADB: `adb shell dumpsys window | findstr mCurrentFocus`
- Or check your app's `AndroidManifest.xml`

### 3. Start Android Emulator

```bash
# List available emulators
emulator -list-avds

# Start an emulator (replace <avd_name> with your emulator name)
emulator -avd <avd_name>
```

Or start from Android Studio: Tools → Device Manager → Start emulator

### 4. Verify ADB Connection

```bash
adb devices
```

You should see your emulator listed:
```
List of devices attached
emulator-5554    device
```

### 5. Start Appium Server

Open a new terminal:
```bash
appium
```

Server should start on `http://localhost:4723`

### 6. Install Your App (First Time Only)

```bash
adb install path\to\your\app.apk
```

Or install manually through the emulator.

### 7. Manual Login (First Time Only)

1. Launch your app manually in the emulator
2. Log in with your credentials
3. The framework is configured with `noReset: true` to preserve this login state

## Usage

### Run All Tests

```bash
python main.py
```

### Run Specific Test File

```bash
python main.py tests/test_login.py
```

### Run Specific Test

```bash
python main.py tests/test_login.py::TestHomeScreen::test_home_screen_visible
```

### Run with Pytest Directly

```bash
pytest tests/ -v
```

### View Logs

Logs are saved in `logs/` directory with timestamps.

## Customizing for Your App

### 1. Update Locators

Edit page objects in `pages/` directory:

**Example in `pages/home_page.py`:**
```python
HOME_TITLE = ("id", "com.example.myapp:id/home_title")
```

**Locator Types:**
- `id`: Resource ID
- `xpath`: XPath expression
- `accessibility_id`: Content description
- `class_name`: Android class name
- `android_uiautomator`: UiAutomator2 selector

### 2. Find Element Locators

**Using Appium Inspector:**
1. Start Appium server
2. Open Appium Inspector
3. Connect to your app
4. Inspect elements and copy locators

**Using ADB:**
```bash
adb shell uiautomator dump
adb pull /sdcard/window_dump.xml
```

### 3. Add New Page Objects

1. Create new file in `pages/` directory
2. Inherit from `BasePage`
3. Define locators and methods
4. Use in your tests

**Example:**
```python
from .base_page import BasePage

class ProfilePage(BasePage):
    EDIT_BUTTON = ("id", "com.example.myapp:id/edit_button")
    
    def tap_edit_button(self):
        self.tap(*self.EDIT_BUTTON)
```

### 4. Add New Tests

Create test files in `tests/` directory:

```python
import pytest
from pages.home_page import HomePage

def test_my_feature(home_page):
    # Your test logic
    assert home_page.is_home_screen_visible()
```

## Important Notes

### Login State Preservation

The framework is configured to preserve login state:
- `noReset: true` - App data is not cleared
- `fullReset: false` - App is not reinstalled

**If you need to reset login:**
1. Manually log out in the app, OR
2. Temporarily set `noReset: false` in `config/settings.yaml`, OR
3. Uninstall and reinstall the app: `adb uninstall com.example.myapp`

### Troubleshooting

**Appium connection fails:**
- Verify Appium server is running: `http://localhost:4723`
- Check emulator is running: `adb devices`
- Verify app package/activity in `config/settings.yaml`

**Element not found:**
- Use Appium Inspector to verify locators
- Check if element is visible (may need to scroll or wait)
- Try alternative locator strategies (xpath, accessibility_id)

**Tests fail immediately:**
- Ensure app is installed on emulator
- Verify login was completed manually
- Check logs in `logs/` directory for detailed error messages

## Project Structure

```
.
  config/
    settings.yaml          # Configuration file
  drivers/
    __init__.py
    driver_factory.py      # Appium driver management
  pages/
    __init__.py
    base_page.py           # Base page with common methods
    login_page.py          # Login page (reference only)
    home_page.py           # Home page object
  tests/
    __init__.py
    test_login.py          # Test cases
  logs/                    # Generated at runtime
  main.py                  # Entry point
  requirements.txt         # Python dependencies
  README.md                # This file
```

## Extending the Framework

### Adding New Interactions

Extend `BasePage` class with new methods:

```python
def long_press(self, locator_type, locator_value):
    element = self.find_element(locator_type, locator_value)
    self.driver.tap([(element.location['x'], element.location['y'])], 2000)
```

### Adding Screenshot on Failure

Modify `main.py` or use pytest hooks:

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        # Take screenshot
        driver.save_screenshot(f"screenshots/{item.name}.png")
```

## License

This framework is provided as-is for automation purposes.

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Verify Appium server and emulator are running
3. Ensure all prerequisites are installed correctly
4. Review `config/settings.yaml` for correct app configuration

