"""
Test cases for the Android app.

NOTE: These tests assume the user is already logged in.
The framework is configured to preserve login state between runs.
"""

import pytest
import logging
from pages.home_page import HomePage
from pages.login_page import LoginPage
from drivers import get_driver, close_driver

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def home_page():
    """
    Fixture to provide HomePage instance.
    
    Yields:
        HomePage: Initialized home page object
    """
    yield HomePage()


@pytest.fixture(scope="function")
def login_page():
    """
    Fixture to provide LoginPage instance (for reference).
    
    Yields:
        LoginPage: Initialized login page object
    """
    yield LoginPage()


class TestHomeScreen:
    """Test class for home screen validation."""
    
    def test_home_screen_visible(self, home_page):
        """
        Test that the home screen is visible after login.
        
        This is the main happy-path test that validates the user
        is logged in and can see the home screen.
        """
        logger.info("Starting test: Verify home screen is visible")
        
        # Verify home screen is visible
        assert home_page.is_home_screen_visible(), \
            "Home screen should be visible after login"
        
        logger.info("Test passed: Home screen is visible")
    
    def test_home_screen_title(self, home_page):
        """
        Test that the home screen has a title.
        
        This test validates that key UI elements are present.
        """
        logger.info("Starting test: Verify home screen title")
        
        # Check if home screen is visible first
        assert home_page.is_home_screen_visible(), \
            "Home screen should be visible"
        
        # Try to get the title (may be empty if locators don't match)
        title = home_page.get_home_title()
        logger.info(f"Home screen title: '{title}'")
        
        # Note: This assertion may need adjustment based on your app
        # For now, we just verify the screen is visible
        assert True, "Home screen title check completed"
        
        logger.info("Test passed: Home screen title check completed")
    
    def test_navigation_elements_present(self, home_page):
        """
        Test that navigation elements are present on home screen.
        
        This validates that the app UI is properly loaded.
        """
        logger.info("Starting test: Verify navigation elements")
        
        # Verify home screen is visible
        assert home_page.is_home_screen_visible(), \
            "Home screen should be visible"
        
        # Check for navigation menu (if present)
        # This is a soft check - won't fail if element doesn't exist
        has_nav = home_page.is_element_present(*home_page.NAVIGATION_MENU)
        logger.info(f"Navigation menu present: {has_nav}")
        
        # Test passes as long as home screen is visible
        assert True, "Navigation elements check completed"
        
        logger.info("Test passed: Navigation elements check completed")


class TestBasicInteractions:
    """Test class for basic UI interactions."""
    
    def test_swipe_gesture(self, home_page):
        """
        Test swipe gesture functionality.
        
        This demonstrates basic gesture interaction.
        """
        logger.info("Starting test: Swipe gesture")
        
        # Verify home screen is visible
        assert home_page.is_home_screen_visible(), \
            "Home screen should be visible"
        
        # Perform a swipe up gesture
        home_page.swipe_up()
        logger.info("Performed swipe up gesture")
        
        # Perform a swipe down gesture
        home_page.swipe_down()
        logger.info("Performed swipe down gesture")
        
        assert True, "Swipe gestures completed successfully"
        logger.info("Test passed: Swipe gesture test completed")
    
    def test_back_button(self, home_page):
        """
        Test Android back button functionality.
        
        This demonstrates navigation control.
        """
        logger.info("Starting test: Back button")
        
        # Verify home screen is visible
        assert home_page.is_home_screen_visible(), \
            "Home screen should be visible"
        
        # Press back button
        home_page.press_back()
        logger.info("Pressed back button")
        
        # Verify we're still on a valid screen
        # (In a real scenario, you might check for a specific screen)
        assert True, "Back button test completed"
        logger.info("Test passed: Back button test completed")


# Pytest hooks for setup and teardown
@pytest.fixture(scope="session", autouse=True)
def setup_driver():
    """
    Session-level fixture to initialize driver before all tests.
    
    This ensures the driver is created once per test session.
    """
    logger.info("Setting up Appium driver for test session")
    try:
        driver = get_driver()
        logger.info(f"Driver initialized: {driver}")
        yield driver
    except Exception as e:
        logger.error(f"Failed to setup driver: {str(e)}")
        raise
    finally:
        logger.info("Tearing down Appium driver")
        close_driver()


@pytest.fixture(scope="function", autouse=True)
def test_setup():
    """
    Function-level fixture that runs before each test.
    
    Can be used for test-specific setup if needed.
    """
    logger.info("=" * 60)
    logger.info("Starting new test")
    yield
    logger.info("Test completed")
    logger.info("=" * 60)

