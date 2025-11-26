# Android Automation Framework - Complete Overview

## 1. HIGH-LEVEL ARCHITECTURE & FILE STRUCTURE

### 1.1 Architecture Description

- **Config layer**: YAML-based configuration for Appium capabilities, device settings, and app identifiers. Centralized settings management with `settings.yaml` containing all Appium capabilities, timeouts, and logging configuration.

- **Driver layer**: Factory pattern for creating and managing Appium WebDriver instances. `DriverFactory` class handles connection to Android emulator/device via ADB, manages driver lifecycle, and ensures proper initialization with preserved login state (`noReset: true`, `fullReset: false`).

- **Page Object layer**: Base page class (`BasePage`) with common UI interaction methods (tap, swipe, text entry, element finding). Specific page classes (`LoginPage`, `HomePage`) inherit from base and encapsulate page-specific logic and locators. Follows Page Object Model pattern for maintainability.

- **Test layer**: Pytest-based test cases that use page objects to perform user flows. Tests focus on validation and assertions. Includes fixtures for setup/teardown and session management. Main happy-path test assumes user is already logged in and validates home screen.

- **Entry point**: `main.py` script initializes logging, runs tests via pytest, handles cleanup, and provides structured output. Configures both file and console logging with timestamps.

- **Logging approach**: Structured logging with file and console handlers. All actions, errors, and test results logged with timestamps. Log files saved in `logs/` directory with timestamped filenames. Configurable log levels via YAML config.

### 1.2 File Structure

```text
.
  config/
    settings.yaml
  drivers/
    __init__.py
    driver_factory.py
  pages/
    __init__.py
    base_page.py
    login_page.py
    home_page.py
  tests/
    __init__.py
    test_login.py
  logs/
    (generated at runtime)
  main.py
  requirements.txt
  README.md
  ARCHITECTURE.md
  FRAMEWORK_OVERVIEW.md
```

---

## 2. IMPLEMENTATION

All code files have been created in the root directory. Key implementation details:

### Configuration (`config/settings.yaml`)
- Appium server URL and timeouts
- Android platform configuration
- App package and activity (placeholders: `com.example.myapp`)
- **Login state preservation**: `noReset: true`, `fullReset: false`
- Logging and timeout settings

### Driver Factory (`drivers/driver_factory.py`)
- Singleton pattern for driver management
- Loads configuration from YAML
- Creates Appium WebDriver with UiAutomator2
- Configures capabilities for login state preservation
- Provides convenience functions: `get_driver()`, `close_driver()`

### Base Page (`pages/base_page.py`)
- Common UI interaction methods:
  - `find_element()` / `find_elements()` - Element location with multiple locator types
  - `tap()` / `tap_element()` - Tap interactions
  - `enter_text()` - Text input
  - `get_text()` - Text retrieval
  - `swipe()` / `swipe_up()` / `swipe_down()` / `swipe_left()` / `swipe_right()` - Gesture support
  - `is_element_present()` - Element visibility checks
  - `press_back()` / `press_home()` - Navigation controls
  - `take_screenshot()` - Screenshot capability
- Supports multiple locator strategies: id, xpath, class_name, accessibility_id, android_uiautomator
- Built-in wait mechanisms and error handling

### Page Objects
- **LoginPage** (`pages/login_page.py`): Reference implementation (not used in automated tests, login done manually)
- **HomePage** (`pages/home_page.py`): Main page object with methods to validate home screen visibility and interact with home screen elements

### Tests (`tests/test_login.py`)
- `TestHomeScreen` class:
  - `test_home_screen_visible()` - Main happy-path test validating user is logged in
  - `test_home_screen_title()` - Validates UI elements are present
  - `test_navigation_elements_present()` - Checks navigation components
- `TestBasicInteractions` class:
  - `test_swipe_gesture()` - Demonstrates swipe functionality
  - `test_back_button()` - Tests Android back button
- Pytest fixtures for driver setup/teardown and test isolation

### Entry Point (`main.py`)
- Initializes structured logging (file + console)
- Loads and validates configuration
- Runs pytest with appropriate arguments
- Handles cleanup and error reporting
- Returns proper exit codes

### Dependencies (`requirements.txt`)
- Appium-Python-Client >= 3.1.0
- Selenium >= 4.15.0
- PyYAML >= 6.0.1
- pytest >= 7.4.3
- Optional: pytest-html, pytest-xdist, colorlog

---

## 3. SETUP & USAGE GUIDE

### Prerequisites Installation

1. **Python 3.11+**: Install from python.org, add to PATH

2. **Android Development Tools**:
   - Install Android Studio from developer.android.com
   - Android SDK and ADB included
   - Add to PATH: `C:\Users\<YourUsername>\AppData\Local\Android\Sdk\platform-tools`

3. **Node.js**: Install from nodejs.org (required for Appium)

4. **Appium**:
   ```bash
   npm install -g appium
   npm install -g @appium/uiautomator2-driver
   ```

5. **Appium Inspector** (Optional): Download from GitHub releases for element inspection

### Framework Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your app** in `config/settings.yaml`:
   - Update `platform_version` to match your emulator
   - Update `app_package` with your app's package name
   - Update `app_activity` with your app's main activity

3. **Start Android emulator**:
   ```bash
   emulator -list-avds  # List available emulators
   emulator -avd <avd_name>  # Start emulator
   ```

4. **Verify ADB connection**:
   ```bash
   adb devices  # Should show your emulator
   ```

5. **Start Appium server** (new terminal):
   ```bash
   appium  # Runs on http://localhost:4723
   ```

6. **Install your app** (first time only):
   ```bash
   adb install path\to\your\app.apk
   ```

7. **Manual login** (first time only):
   - Launch app manually in emulator
   - Log in with credentials
   - Framework preserves this login state

### Running Tests

**Run all tests**:
```bash
python main.py
```

**Run specific test file**:
```bash
python main.py tests/test_login.py
```

**Run specific test**:
```bash
python main.py tests/test_login.py::TestHomeScreen::test_home_screen_visible
```

**Run with pytest directly**:
```bash
pytest tests/ -v
```

### Customizing for Your App

1. **Update locators** in page objects:
   - Use Appium Inspector to find element locators
   - Update locator tuples in page classes (e.g., `HOME_TITLE = ("id", "com.example.myapp:id/home_title")`)

2. **Add new page objects**:
   - Create new file in `pages/` directory
   - Inherit from `BasePage`
   - Define locators and methods

3. **Add new tests**:
   - Create test files in `tests/` directory
   - Use pytest fixtures and page objects

### Finding Element Locators

**Using Appium Inspector**:
1. Start Appium server
2. Open Appium Inspector
3. Connect to your app
4. Inspect elements and copy locators

**Using ADB**:
```bash
adb shell uiautomator dump
adb pull /sdcard/window_dump.xml
```

### Important Notes

- **Login state is preserved** between runs via `noReset: true` and `fullReset: false`
- **To reset login**: Manually log out, or temporarily set `noReset: false` in config
- **Logs are saved** in `logs/` directory with timestamps
- **Troubleshooting**: Check logs, verify Appium server is running, ensure emulator is connected

### Project Structure Summary

- `config/` - Configuration files
- `drivers/` - Appium driver management
- `pages/` - Page Object Model classes
- `tests/` - Test cases
- `logs/` - Generated log files
- `main.py` - Entry point
- `requirements.txt` - Python dependencies
- `README.md` - Detailed documentation

---

## Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Android Studio and SDK installed
- [ ] ADB in PATH
- [ ] Node.js installed
- [ ] Appium installed globally
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] App configured in `config/settings.yaml`
- [ ] Android emulator running
- [ ] ADB connection verified (`adb devices`)
- [ ] Appium server running (`appium`)
- [ ] App installed on emulator
- [ ] Manual login completed
- [ ] Ready to run tests (`python main.py`)

---

For detailed information, see `README.md`.

