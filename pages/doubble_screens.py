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
        IMPROVED: Prioritizes swipe screen detection with multiple indicators.
        
        Returns:
            str: Screen name ('home', 'swipe', 'login', 'unknown')
        """
        try:
            # CRITICAL: Check for swipe screen FIRST (most important to detect correctly)
            # Strategy 1: Check like button (heart button on swipe screen)
            try:
                if self.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.1):
                    logger.info("Detected: SWIPE screen (found like button)")
                    return "swipe"
            except:
                pass
            
            # Strategy 2: Check for swipe/discover/explore elements
            swipe_text_indicators = [
                "//*[contains(@content-desc, 'Swipe') or contains(@content-desc, 'swipe')]",
                "//*[contains(@content-desc, 'Discover') or contains(@content-desc, 'discover')]",
                "//*[contains(@content-desc, 'Explore') or contains(@content-desc, 'explore')]",
                "//*[contains(@text, 'Swipe') or contains(@text, 'swipe')]",
            ]
            
            for xpath in swipe_text_indicators[:2]:  # Check first 2
                try:
                    if self.is_element_present_silent("xpath", xpath, timeout=0.05):
                        logger.info(f"Detected: SWIPE screen (found swipe/discover/explore element)")
                        return "swipe"
                except:
                    continue
            
            # Strategy 3: Check for card stack (common on swipe screens)
            try:
                if self.is_element_present_silent("xpath", "//*[@class='androidx.cardview.widget.CardView']", timeout=0.05):
                    logger.info("Detected: SWIPE screen (found card view)")
                    return "swipe"
            except:
                pass
            
            # Strategy 4: Check swipe screen indicators from list
            for locator_type, locator_value in self.SWIPE_SCREEN_INDICATORS[:2]:  # Check first 2
                try:
                    if self.is_element_present_silent(locator_type, locator_value, timeout=0.05):
                        logger.info(f"Detected: SWIPE screen (found: {locator_type}={locator_value})")
                        return "swipe"
                except:
                    continue
            
            # Only check for home/login if swipe not found
            # Check for home screen - only check top 1 indicator with reduced timeout
            for locator_type, locator_value in self.HOME_SCREEN_INDICATORS[:1]:
                try:
                    if self.is_element_present_silent(locator_type, locator_value, timeout=0.1):
                        logger.info(f"Detected: HOME screen (found: {locator_type}={locator_value})")
                        return "home"
                except Exception:
                    continue
            
            # Check for login screen - only check top 1 indicator with reduced timeout
            for locator_type, locator_value in self.LOGIN_SCREEN_INDICATORS[:1]:
                try:
                    if self.is_element_present_silent(locator_type, locator_value, timeout=0.1):
                        logger.info(f"Detected: LOGIN screen (found: {locator_type}={locator_value})")
                        return "login"
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Error during screen detection: {e}")
            return "unknown"
        
        # Skip page source check - too slow, just return unknown
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

