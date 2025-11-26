"""Login page object - for reference only (login is done manually)."""

import logging
from .base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """
    Login page object.
    
    NOTE: This class exists for reference but login is performed manually.
    The framework is configured to preserve login state between runs.
    """
    
    # Locator examples (update these based on your actual app)
    USERNAME_FIELD = ("id", "com.example.myapp:id/username")
    PASSWORD_FIELD = ("id", "com.example.myapp:id/password")
    LOGIN_BUTTON = ("id", "com.example.myapp:id/login_button")
    SKIP_BUTTON = ("id", "com.example.myapp:id/skip_button")
    
    def is_login_screen_visible(self) -> bool:
        """
        Check if login screen is currently visible.
        
        Returns:
            bool: True if login screen elements are present
        """
        try:
            return (
                self.is_element_present(*self.USERNAME_FIELD) or
                self.is_element_present(*self.LOGIN_BUTTON)
            )
        except Exception as e:
            logger.warning(f"Error checking login screen: {str(e)}")
            return False
    
    def enter_username(self, username: str):
        """Enter username (for reference only - not used in automated tests)."""
        self.enter_text(*self.USERNAME_FIELD, username)
    
    def enter_password(self, password: str):
        """Enter password (for reference only - not used in automated tests)."""
        self.enter_text(*self.PASSWORD_FIELD, password)
    
    def tap_login_button(self):
        """Tap login button (for reference only - not used in automated tests)."""
        self.tap(*self.LOGIN_BUTTON)

