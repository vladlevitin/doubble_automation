"""
Quick test script to open Doubble app and perform a swipe.
Run this to test the automation framework with the Doubble app.
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from drivers import DriverFactory, get_driver, close_driver
from pages.base_page import BasePage
from pages.doubble_screens import DoubbleScreenDetector
from pages.doubble_swipe_page import DoubbleSwipePage
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Open Doubble app and perform a swipe."""
    try:
        logger.info("=" * 60)
        logger.info("Opening Doubble App and Performing Swipe")
        logger.info("=" * 60)
        
        # Initialize driver
        logger.info("Initializing Appium driver...")
        driver = get_driver()
        logger.info("Driver initialized successfully")
        
        # Create base page, screen detector, and swipe page
        page = BasePage()
        screen_detector = DoubbleScreenDetector()
        swipe_page = DoubbleSwipePage()
        
        # Wait a moment for everything to settle
        time.sleep(2)
        
        # Get current app info
        try:
            current_package = page.get_current_package()
            current_activity = page.get_current_activity()
            logger.info(f"Current app: {current_package}/{current_activity}")
        except Exception as e:
            logger.warning(f"Could not get current app info: {e}")
        
        # Launch the Doubble app
        logger.info("Launching Doubble app...")
        try:
            driver.activate_app("dk.doubble.dating")
            logger.info("App activated")
        except Exception as e:
            logger.warning(f"activate_app failed: {e}")
            # Fallback: use ADB to start activity
            import subprocess
            adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
            if adb_path.exists():
                subprocess.run([str(adb_path), "shell", "am", "start", "-n", "dk.doubble.dating/.MainActivity"], 
                             capture_output=True)
                logger.info("App started via ADB")
        
        # Wait for app to load
        logger.info("Waiting for app to load...")
        time.sleep(5)
        
        # Detect current screen
        logger.info("=" * 60)
        logger.info("Detecting current screen...")
        logger.info("=" * 60)
        
        screen_info = screen_detector.get_screen_info()
        current_screen = screen_info["screen"]
        logger.info(f"Current screen: {current_screen}")
        logger.info(f"Package: {screen_info.get('package', 'unknown')}")
        logger.info(f"Activity: {screen_info.get('activity', 'unknown')}")
        
        # Only look for swipe button if we're on home screen
        if current_screen == "home":
            logger.info("=" * 60)
            logger.info("On HOME screen - Looking for swipe button to click...")
            logger.info("=" * 60)
            
            # Import the find function
            try:
                from find_and_click_swipe_button import find_swipe_button
                
                button_locator = find_swipe_button(page)
                
                if button_locator:
                    locator_type, locator_value = button_locator
                    logger.info(f"Found swipe button! Clicking: {locator_type}={locator_value}")
                    page.tap(locator_type, locator_value)
                    logger.info("Swipe button clicked!")
                    time.sleep(3)  # Wait for UI to update after button click
                    
                    # Re-detect screen after clicking
                    new_screen = screen_detector.detect_current_screen()
                    logger.info(f"Screen after button click: {new_screen}")
                else:
                    logger.warning("Could not find swipe button on home screen")
            except Exception as e:
                logger.warning(f"Error finding swipe button: {e}")
        elif current_screen == "swipe":
            logger.info("Already on SWIPE screen - will click like button and handle pop-ups!")
        elif current_screen == "login":
            logger.warning("On LOGIN screen - user needs to log in manually first!")
            logger.warning("Please log in manually, then run the script again.")
            return 1
        else:
            logger.warning(f"Unknown screen ({current_screen}) - attempting to continue...")
        
        # On swipe screen: Click like button and handle pop-ups
        logger.info("=" * 60)
        logger.info("Clicking like button and handling pop-ups...")
        logger.info("=" * 60)
        
        # Click like button multiple times (simulating user interactions)
        for i in range(3):
            logger.info(f"Like button click #{i+1}...")
            if swipe_page.click_like_button():
                logger.info(f"Like button clicked successfully (#{i+1})")
                time.sleep(2)  # Wait between clicks
            else:
                logger.warning(f"Could not click like button (#{i+1})")
                break
        
        # Perform swipe gestures as well
        logger.info("=" * 60)
        logger.info("Performing swipe gestures...")
        logger.info("=" * 60)
        
        logger.info("Swiping LEFT (swipe left to pass)...")
        page.swipe_left()
        time.sleep(2)
        swipe_page.handle_popups()  # Check for pop-ups after swipe
        
        logger.info("Swiping RIGHT (swipe right to like)...")
        page.swipe_right()
        time.sleep(2)
        swipe_page.handle_popups()  # Check for pop-ups after swipe
        
        logger.info("Swiping UP...")
        page.swipe_up()
        time.sleep(2)
        swipe_page.handle_popups()  # Check for pop-ups after swipe
        
        logger.info("=" * 60)
        logger.info("Swipe test completed successfully!")
        logger.info("=" * 60)
        
        # Keep app open for a few seconds so you can see it
        logger.info("Keeping app open for 5 seconds...")
        time.sleep(5)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        return 1
    finally:
        logger.info("Cleaning up...")
        close_driver()
        logger.info("Done!")


if __name__ == "__main__":
    sys.exit(main())

