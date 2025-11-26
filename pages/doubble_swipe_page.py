"""
Doubble swipe screen page object.
Handles interactions on the swipe/card screen.
"""

import logging
import time
from .base_page import BasePage

logger = logging.getLogger(__name__)


class DoubbleSwipePage(BasePage):
    """Page object for the swipe/card screen in Doubble app."""
    
    # Like button locators - multiple strategies
    LIKE_BUTTON_LOCATORS = [
        ("id", "dk.doubble.dating:id/like"),
        ("id", "dk.doubble.dating:id/like_button"),
        ("id", "dk.doubble.dating:id/btn_like"),
        ("accessibility_id", "Like"),
        ("accessibility_id", "like"),
        ("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]"),
        ("xpath", "//*[contains(@text, 'Like')]"),
    ]
    
    # Pop-up/dialog close/cancel button locators
    POPUP_CLOSE_LOCATORS = [
        ("id", "dk.doubble.dating:id/close"),
        ("id", "dk.doubble.dating:id/cancel"),
        ("id", "dk.doubble.dating:id/dismiss"),
        ("id", "dk.doubble.dating:id/close_button"),
        ("accessibility_id", "Close"),
        ("accessibility_id", "Cancel"),
        ("accessibility_id", "Dismiss"),
        ("xpath", "//*[contains(@text, 'Close') or contains(@text, 'Cancel') or contains(@text, 'Dismiss')]"),
        ("xpath", "//*[contains(@content-desc, 'Close') or contains(@content-desc, 'Cancel')]"),
        # Android system buttons
        ("xpath", "//android.widget.Button[@text='Cancel']"),
        ("xpath", "//android.widget.Button[@text='Close']"),
        ("xpath", "//android.widget.ImageButton[@content-desc='Close']"),
    ]
    
    def find_like_button(self):
        """
        Find the like button using multiple strategies.
        
        Returns:
            tuple: (locator_type, locator_value) or None
        """
        logger.info("Searching for like button...")
        
        for locator_type, locator_value in self.LIKE_BUTTON_LOCATORS:
            if self.is_element_present(locator_type, locator_value, timeout=2):
                logger.info(f"Found like button: {locator_type}={locator_value}")
                return (locator_type, locator_value)
        
        # Try to find by UI hierarchy analysis
        try:
            source = self.driver.page_source
            if source:
                source_lower = source.lower()
                # Look for like-related elements
                if 'like' in source_lower:
                    # Try common patterns
                    elements = self.driver.find_elements("xpath", "//*[contains(@resource-id, 'like')]")
                    if elements:
                        resource_id = elements[0].get_attribute('resource-id')
                        if resource_id:
                            logger.info(f"Found like button by resource-id: {resource_id}")
                            return ("id", resource_id)
        except Exception as e:
            logger.warning(f"Error analyzing UI for like button: {e}")
        
        logger.warning("Could not find like button")
        return None
    
    def click_like_button(self):
        """
        Click the like button.
        
        Returns:
            bool: True if button was found and clicked, False otherwise
        """
        button_locator = self.find_like_button()
        
        if button_locator:
            locator_type, locator_value = button_locator
            logger.info(f"Clicking like button: {locator_type}={locator_value}")
            self.tap(locator_type, locator_value)
            time.sleep(1)  # Wait for action to complete
            
            # Check for pop-ups after clicking
            self.handle_popups()
            
            return True
        else:
            logger.warning("Like button not found - cannot click")
            return False
    
    def handle_popups(self, max_attempts=3):
        """
        Handle any pop-ups that appear by dismissing/canceling them.
        
        Args:
            max_attempts: Maximum number of pop-ups to dismiss
        """
        logger.info("Checking for pop-ups...")
        
        for attempt in range(max_attempts):
            popup_found = False
            
            # Try to find and close pop-ups
            for locator_type, locator_value in self.POPUP_CLOSE_LOCATORS:
                if self.is_element_present(locator_type, locator_value, timeout=1):
                    logger.info(f"Found pop-up close button: {locator_type}={locator_value}")
                    try:
                        self.tap(locator_type, locator_value)
                        logger.info("Pop-up dismissed")
                        popup_found = True
                        time.sleep(0.5)
                        break
                    except Exception as e:
                        logger.warning(f"Error dismissing pop-up: {e}")
            
            # Also try pressing back button as fallback
            if popup_found:
                time.sleep(0.5)
                # Check if pop-up is still there
                still_present = any(
                    self.is_element_present(loc_type, loc_value, timeout=1)
                    for loc_type, loc_value in self.POPUP_CLOSE_LOCATORS[:5]  # Check first few
                )
                if not still_present:
                    logger.info("Pop-up successfully dismissed")
                    break
            else:
                # No pop-up found, we're done
                break
        
        if not popup_found:
            logger.info("No pop-ups detected")

