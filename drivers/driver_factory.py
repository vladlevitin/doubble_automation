"""Driver factory for creating and managing Appium WebDriver instances."""

import os
import yaml
from pathlib import Path
from typing import Optional, Any

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


class DriverFactory:
    """Factory class for creating Appium WebDriver instances."""
    
    _driver: Optional[Any] = None
    _config: dict = None
    
    @classmethod
    def load_config(cls) -> dict:
        """Load configuration from settings.yaml."""
        if cls._config is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                cls._config = yaml.safe_load(f)
        return cls._config
    
    @classmethod
    def create_driver(cls) -> Any:
        """
        Create and return an Appium WebDriver instance.
        
        Returns:
            webdriver.WebDriver: Configured Appium driver instance
            
        Raises:
            Exception: If driver creation fails
        """
        if cls._driver is not None:
            return cls._driver
        
        config = cls.load_config()
        appium_config = config["appium"]
        android_config = config["android"]
        
        # Configure Appium options
        options = UiAutomator2Options()
        options.platform_name = android_config["platform_name"]
        options.platform_version = android_config["platform_version"]
        options.device_name = android_config["device_name"]
        options.automation_name = android_config["automation_name"]
        
        # App configuration
        options.app_package = android_config["app_package"]
        options.app_activity = android_config["app_activity"]
        
        # IMPORTANT: Preserve login state
        options.no_reset = android_config["no_reset"]
        options.full_reset = android_config["full_reset"]
        
        # Additional capabilities
        options.auto_grant_permissions = android_config.get("auto_grant_permissions", True)
        options.skip_unlock = android_config.get("skip_unlock", True)
        options.uiautomator2_server_launch_timeout = android_config.get(
            "uiautomator2_server_launch_timeout", 20000
        )
        
        # Set timeouts
        options.new_command_timeout = appium_config["new_command_timeout"]
        
        # Create driver
        try:
            cls._driver = webdriver.Remote(
                command_executor=appium_config["server_url"],
                options=options
            )
            
            # Set implicit wait
            implicit_wait = config["timeouts"]["implicit_wait"]
            cls._driver.implicitly_wait(implicit_wait)
            
            return cls._driver
        except Exception as e:
            raise Exception(f"Failed to create Appium driver: {str(e)}")
    
    @classmethod
    def get_driver(cls) -> Optional[Any]:
        """Get the current driver instance, creating it if necessary."""
        if cls._driver is None:
            return cls.create_driver()
        return cls._driver
    
    @classmethod
    def close_driver(cls):
        """Close and cleanup the driver instance."""
        if cls._driver is not None:
            try:
                cls._driver.quit()
            except Exception as e:
                print(f"Error closing driver: {str(e)}")
            finally:
                cls._driver = None


# Convenience functions
def get_driver() -> Any:
    """Get or create the Appium driver instance."""
    return DriverFactory.get_driver()


def close_driver():
    """Close the Appium driver instance."""
    DriverFactory.close_driver()

