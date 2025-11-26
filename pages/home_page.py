"""Home page object for the main app screen."""

import logging
from .base_page import BasePage

logger = logging.getLogger(__name__)


class HomePage(BasePage):
    """Home page object representing the main screen after login."""
    
    # Locator examples (update these based on your actual app)
    # These are placeholder locators - replace with your app's actual element identifiers
    HOME_TITLE = ("id", "com.example.myapp:id/home_title")
    NAVIGATION_MENU = ("id", "com.example.myapp:id/nav_menu")
    PROFILE_BUTTON = ("id", "com.example.myapp:id/profile_button")
    SEARCH_BAR = ("id", "com.example.myapp:id/search_bar")
    
    # Alternative locators using different strategies
    HOME_TITLE_XPATH = ("xpath", "//android.widget.TextView[@text='Home']")
    HOME_TITLE_ACCESSIBILITY = ("accessibility_id", "Home Screen Title")
    
    def is_home_screen_visible(self) -> bool:
        """
        Verify that the home screen is visible.
        
        This method checks for key elements that should be present
        on the home screen to confirm the user is logged in.
        
        Returns:
            bool: True if home screen elements are present
        """
        try:
            # Try multiple locator strategies for robustness
            is_visible = (
                self.is_element_present(*self.HOME_TITLE) or
                self.is_element_present(*self.HOME_TITLE_XPATH) or
                self.is_element_present(*self.HOME_TITLE_ACCESSIBILITY) or
                self.is_element_present(*self.NAVIGATION_MENU)
            )
            
            if is_visible:
                logger.info("Home screen is visible")
            else:
                logger.warning("Home screen elements not found")
            
            return is_visible
        except Exception as e:
            logger.error(f"Error checking home screen visibility: {str(e)}")
            return False
    
    def get_home_title(self) -> str:
        """
        Get the home screen title text.
        
        Returns:
            str: Title text, or empty string if not found
        """
        try:
            # Try different locator strategies
            if self.is_element_present(*self.HOME_TITLE):
                return self.get_text(*self.HOME_TITLE)
            elif self.is_element_present(*self.HOME_TITLE_XPATH):
                return self.get_text(*self.HOME_TITLE_XPATH)
            elif self.is_element_present(*self.HOME_TITLE_ACCESSIBILITY):
                return self.get_text(*self.HOME_TITLE_ACCESSIBILITY)
            return ""
        except Exception as e:
            logger.warning(f"Could not get home title: {str(e)}")
            return ""
    
    def tap_profile_button(self):
        """Tap the profile button."""
        if self.is_element_present(*self.PROFILE_BUTTON):
            self.tap(*self.PROFILE_BUTTON)
            logger.info("Tapped profile button")
        else:
            logger.warning("Profile button not found")
    
    def tap_navigation_menu(self):
        """Tap the navigation menu button."""
        if self.is_element_present(*self.NAVIGATION_MENU):
            self.tap(*self.NAVIGATION_MENU)
            logger.info("Tapped navigation menu")
        else:
            logger.warning("Navigation menu not found")
    
    def enter_search_query(self, query: str):
        """
        Enter a search query in the search bar.
        
        Args:
            query: Search query text
        """
        if self.is_element_present(*self.SEARCH_BAR):
            self.enter_text(*self.SEARCH_BAR, query)
            logger.info(f"Entered search query: {query}")
        else:
            logger.warning("Search bar not found")

