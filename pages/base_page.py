"""Base page class with common UI interaction methods."""

import time
from typing import Optional, Tuple
from appium.webdriver import WebElement
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from drivers import get_driver
import logging


logger = logging.getLogger(__name__)


class BasePage:
    """Base class for all page objects with common UI interaction methods."""
    
    def __init__(self):
        """Initialize the base page with driver reference."""
        self.driver = get_driver()
        self.wait_timeout = 20  # Default wait timeout in seconds
    
    def find_element(
        self,
        locator_type: str,
        locator_value: str,
        timeout: Optional[int] = None
    ) -> WebElement:
        """
        Find a single element with explicit wait.
        
        Args:
            locator_type: Type of locator (id, xpath, class_name, accessibility_id, etc.)
            locator_value: Value of the locator
            timeout: Optional timeout in seconds (defaults to self.wait_timeout)
            
        Returns:
            WebElement: Found element
            
        Raises:
            TimeoutException: If element is not found within timeout
        """
        timeout = timeout or self.wait_timeout
        wait = WebDriverWait(self.driver, timeout)
        
        # Map string locator types to AppiumBy constants
        locator_map = {
            "id": AppiumBy.ID,
            "xpath": AppiumBy.XPATH,
            "class_name": AppiumBy.CLASS_NAME,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "tag_name": AppiumBy.TAG_NAME,
        }
        
        by = locator_map.get(locator_type.lower())
        if by is None:
            raise ValueError(f"Unsupported locator type: {locator_type}")
        
        try:
            element = wait.until(EC.presence_of_element_located((by, locator_value)))
            logger.debug(f"Found element: {locator_type}={locator_value}")
            return element
        except TimeoutException:
            logger.error(f"Element not found: {locator_type}={locator_value}")
            raise
    
    def find_elements(
        self,
        locator_type: str,
        locator_value: str,
        timeout: Optional[int] = None
    ) -> list[WebElement]:
        """
        Find multiple elements with explicit wait.
        
        Args:
            locator_type: Type of locator
            locator_value: Value of the locator
            timeout: Optional timeout in seconds
            
        Returns:
            list[WebElement]: List of found elements (may be empty)
        """
        timeout = timeout or self.wait_timeout
        wait = WebDriverWait(self.driver, timeout)
        
        locator_map = {
            "id": AppiumBy.ID,
            "xpath": AppiumBy.XPATH,
            "class_name": AppiumBy.CLASS_NAME,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "tag_name": AppiumBy.TAG_NAME,
        }
        
        by = locator_map.get(locator_type.lower())
        if by is None:
            raise ValueError(f"Unsupported locator type: {locator_type}")
        
        try:
            wait.until(EC.presence_of_element_located((by, locator_value)))
            elements = self.driver.find_elements(by, locator_value)
            logger.debug(f"Found {len(elements)} elements: {locator_type}={locator_value}")
            return elements
        except TimeoutException:
            logger.warning(f"No elements found: {locator_type}={locator_value}")
            return []
    
    def tap(self, locator_type: str, locator_value: str, timeout: Optional[int] = None):
        """
        Tap on an element.
        
        Args:
            locator_type: Type of locator
            locator_value: Value of the locator
            timeout: Optional timeout in seconds
        """
        element = self.find_element(locator_type, locator_value, timeout)
        element.click()
        logger.info(f"Tapped on element: {locator_type}={locator_value}")
        time.sleep(0.5)  # Brief pause after action
    
    def tap_element(self, element: WebElement):
        """
        Tap on a WebElement directly.
        
        Args:
            element: WebElement to tap
        """
        element.click()
        logger.info("Tapped on element")
        time.sleep(0.5)
    
    def enter_text(
        self,
        locator_type: str,
        locator_value: str,
        text: str,
        clear_first: bool = True,
        timeout: Optional[int] = None
    ):
        """
        Enter text into an input field.
        
        Args:
            locator_type: Type of locator
            locator_value: Value of the locator
            text: Text to enter
            clear_first: Whether to clear the field first
            timeout: Optional timeout in seconds
        """
        element = self.find_element(locator_type, locator_value, timeout)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.info(f"Entered text '{text}' into {locator_type}={locator_value}")
        time.sleep(0.3)
    
    def get_text(self, locator_type: str, locator_value: str, timeout: Optional[int] = None) -> str:
        """
        Get text from an element.
        
        Args:
            locator_type: Type of locator
            locator_value: Value of the locator
            timeout: Optional timeout in seconds
            
        Returns:
            str: Text content of the element
        """
        element = self.find_element(locator_type, locator_value, timeout)
        text = element.text
        logger.debug(f"Retrieved text '{text}' from {locator_type}={locator_value}")
        return text
    
    def is_element_present(
        self,
        locator_type: str,
        locator_value: str,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Check if an element is present on the page.
        
        Args:
            locator_type: Type of locator
            locator_value: Value of the locator
            timeout: Optional timeout in seconds (defaults to 5 seconds for quick check)
            
        Returns:
            bool: True if element is present, False otherwise
        """
        timeout = timeout or 5
        try:
            self.find_element(locator_type, locator_value, timeout)
            return True
        except (TimeoutException, NoSuchElementException):
            return False
    
    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: int = 1000
    ):
        """
        Perform a swipe gesture.
        
        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Duration of swipe in milliseconds
        """
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
        logger.info(f"Swipe from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        time.sleep(0.5)
    
    def swipe_up(self, duration: int = 1000):
        """Swipe up on the screen."""
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.8)
        end_y = int(size["height"] * 0.2)
        self.swipe(start_x, start_y, start_x, end_y, duration)
    
    def swipe_down(self, duration: int = 1000):
        """Swipe down on the screen."""
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.2)
        end_y = int(size["height"] * 0.8)
        self.swipe(start_x, start_y, start_x, end_y, duration)
    
    def swipe_left(self, duration: int = 1000):
        """Swipe left on the screen."""
        size = self.driver.get_window_size()
        start_x = int(size["width"] * 0.8)
        end_x = int(size["width"] * 0.2)
        start_y = size["height"] // 2
        self.swipe(start_x, start_y, end_x, start_y, duration)
    
    def swipe_right(self, duration: int = 1000):
        """Swipe right on the screen."""
        size = self.driver.get_window_size()
        start_x = int(size["width"] * 0.2)
        end_x = int(size["width"] * 0.8)
        start_y = size["height"] // 2
        self.swipe(start_x, start_y, end_x, start_y, duration)
    
    def wait_for_element(
        self,
        locator_type: str,
        locator_value: str,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Wait for an element to be present.
        
        Args:
            locator_type: Type of locator
            locator_value: Value of the locator
            timeout: Optional timeout in seconds
            
        Returns:
            bool: True if element appears, False if timeout
        """
        return self.is_element_present(locator_type, locator_value, timeout)
    
    def get_current_activity(self) -> str:
        """Get the current activity name."""
        activity = self.driver.current_activity
        logger.debug(f"Current activity: {activity}")
        return activity
    
    def get_current_package(self) -> str:
        """Get the current package name."""
        package = self.driver.current_package
        logger.debug(f"Current package: {package}")
        return package
    
    def press_back(self):
        """Press the Android back button."""
        self.driver.back()
        logger.info("Pressed back button")
        time.sleep(0.5)
    
    def press_home(self):
        """Press the Android home button."""
        self.driver.press_keycode(3)  # KEYCODE_HOME
        logger.info("Pressed home button")
        time.sleep(0.5)
    
    def take_screenshot(self, filename: str):
        """
        Take a screenshot and save it.
        
        Args:
            filename: Path to save the screenshot
        """
        self.driver.save_screenshot(filename)
        logger.info(f"Screenshot saved: {filename}")

