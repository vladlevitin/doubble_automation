# High-Level Architecture & File Structure

## 1.1 Architecture Overview

- **Config layer**: YAML-based configuration for Appium capabilities, device settings, and app identifiers. Centralized settings management.
- **Driver layer**: Factory pattern for creating and managing Appium WebDriver instances. Handles connection to Android emulator/device via ADB.
- **Page Object layer**: Base page class with common UI interaction methods (tap, swipe, text entry). Specific page classes (LoginPage, HomePage) inherit from base and encapsulate page-specific logic.
- **Test layer**: Pytest-based test cases that use page objects to perform user flows. Focuses on validation and assertions.
- **Entry point**: `main.py` script to run tests with proper setup/teardown and logging initialization.
- **Logging approach**: Structured logging with file and console handlers. Logs all actions, errors, and test results with timestamps.

## 1.2 File Structure

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
```

