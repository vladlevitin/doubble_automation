"""
Screen detection for Doubble app.
Identifies which screen the app is currently on.
"""

import logging
from .base_page import BasePage

logger = logging.getLogger(__name__)


class DoubbleScreenDetector(BasePage):
    """Detects which screen is currently displayed in Doubble app."""
    
    # Common screen identifiers - update these based on your app
    HOME_SCREEN_INDICATORS = [
        ("id", "dk.doubble.dating:id/home"),
        ("id", "dk.doubble.dating:id/main"),
        ("xpath", "//*[contains(@text, 'Home')]"),
        ("xpath", "//*[contains(@content-desc, 'Home')]"),
    ]
    
    SWIPE_SCREEN_INDICATORS = [
        ("id", "dk.doubble.dating:id/swipe"),
        ("id", "dk.doubble.dating:id/card"),
        ("xpath", "//*[contains(@text, 'Swipe')]"),
        ("xpath", "//*[contains(@content-desc, 'Swipe')]"),
    ]
    
    LOGIN_SCREEN_INDICATORS = [
        ("id", "dk.doubble.dating:id/login"),
        ("id", "dk.doubble.dating:id/username"),
        ("id", "dk.doubble.dating:id/password"),
        ("xpath", "//*[contains(@text, 'Login')]"),
        ("xpath", "//*[contains(@text, 'Sign in')]"),
    ]
    
    def detect_current_screen(self) -> str:
        """
        Detect which screen is currently displayed.
        
        Returns:
            str: Screen name ('home', 'swipe', 'login', 'unknown')
        """
        logger.info("Detecting current screen...")
        
        # Check for home screen
        for locator_type, locator_value in self.HOME_SCREEN_INDICATORS:
            if self.is_element_present(locator_type, locator_value, timeout=2):
                logger.info(f"Detected: HOME screen (found: {locator_type}={locator_value})")
                return "home"
        
        # Check for swipe screen
        for locator_type, locator_value in self.SWIPE_SCREEN_INDICATORS:
            if self.is_element_present(locator_type, locator_value, timeout=2):
                logger.info(f"Detected: SWIPE screen (found: {locator_type}={locator_value})")
                return "swipe"
        
        # Check for login screen
        for locator_type, locator_value in self.LOGIN_SCREEN_INDICATORS:
            if self.is_element_present(locator_type, locator_value, timeout=2):
                logger.info(f"Detected: LOGIN screen (found: {locator_type}={locator_value})")
                return "login"
        
        # Try to get UI hierarchy for analysis
        try:
            source = self.driver.page_source
            if source:
                # Analyze page source for clues
                source_lower = source.lower()
                
                if any(keyword in source_lower for keyword in ['home', 'main', 'dashboard']):
                    logger.info("Detected: HOME screen (from page source analysis)")
                    return "home"
                elif any(keyword in source_lower for keyword in ['swipe', 'card', 'profile']):
                    logger.info("Detected: SWIPE screen (from page source analysis)")
                    return "swipe"
                elif any(keyword in source_lower for keyword in ['login', 'sign in', 'username', 'password']):
                    logger.info("Detected: LOGIN screen (from page source analysis)")
                    return "login"
        except Exception as e:
            logger.warning(f"Could not analyze page source: {e}")
        
        logger.warning("Could not detect screen - returning 'unknown'")
        return "unknown"
    
    def is_home_screen(self) -> bool:
        """Check if currently on home screen."""
        return self.detect_current_screen() == "home"
    
    def is_swipe_screen(self) -> bool:
        """Check if currently on swipe screen."""
        return self.detect_current_screen() == "swipe"
    
    def is_login_screen(self) -> bool:
        """Check if currently on login screen."""
        return self.detect_current_screen() == "login"
    
    def get_screen_info(self) -> dict:
        """
        Get detailed information about current screen.
        
        Returns:
            dict: Screen information including current activity, package, and detected screen
        """
        info = {
            "screen": self.detect_current_screen(),
            "package": None,
            "activity": None,
        }
        
        try:
            info["package"] = self.get_current_package()
            info["activity"] = self.get_current_activity()
        except Exception as e:
            logger.warning(f"Could not get package/activity: {e}")
        
        return info

