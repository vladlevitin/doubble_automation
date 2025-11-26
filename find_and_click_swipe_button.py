"""
Script to find and click the swipe button in Doubble app.
Uses UI hierarchy analysis to locate the button.
"""

import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from drivers import DriverFactory, get_driver, close_driver
from pages.base_page import BasePage
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_ui_hierarchy(driver):
    """
    Get the UI hierarchy XML from the device.
    
    Returns:
        str: UI hierarchy XML content
    """
    try:
        # Use ADB to get UI hierarchy
        import subprocess
        adb_path = Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe"
        
        if not adb_path.exists():
            # Try alternative path
            adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
        
        # Get UI dump via Appium
        source = driver.page_source
        return source
    except Exception as e:
        logger.error(f"Error getting UI hierarchy: {e}")
        return None


def find_swipe_button(page):
    """
    Find the swipe button using multiple strategies.
    
    Returns:
        tuple: (locator_type, locator_value) or None
    """
    logger.info("Searching for swipe button...")
    
    # Strategy 1: Search by text content (case-insensitive)
    swipe_texts = ["swipe", "start swiping", "swipe now", "begin", "start"]
    
    for text in swipe_texts:
        # Try by accessibility ID (content description)
        if page.is_element_present("accessibility_id", text):
            logger.info(f"Found swipe button by accessibility_id: {text}")
            return ("accessibility_id", text)
        
        # Try by XPath with text
        xpath = f"//*[contains(@text, '{text}') or contains(@content-desc, '{text}')]"
        if page.is_element_present("xpath", xpath):
            logger.info(f"Found swipe button by XPath text: {text}")
            return ("xpath", xpath)
    
    # Strategy 2: Search by common button IDs
    common_ids = [
        "swipe_button",
        "btn_swipe",
        "start_swipe",
        "swipe",
        "button_swipe",
        "main_button",
        "primary_button"
    ]
    
    for button_id in common_ids:
        # Try with package prefix
        full_id = f"dk.doubble.dating:id/{button_id}"
        if page.is_element_present("id", full_id):
            logger.info(f"Found swipe button by ID: {full_id}")
            return ("id", full_id)
        
        # Try without package prefix
        if page.is_element_present("id", button_id):
            logger.info(f"Found swipe button by ID: {button_id}")
            return ("id", button_id)
    
    # Strategy 3: Get UI hierarchy and analyze
    logger.info("Getting UI hierarchy for analysis...")
    try:
        driver = page.driver
        source = driver.page_source
        
        if source:
            # Parse XML
            root = ET.fromstring(source)
            
            # Search for elements with swipe-related attributes
            for elem in root.iter():
                text = elem.get('text', '').lower()
                content_desc = elem.get('content-desc', '').lower()
                resource_id = elem.get('resource-id', '').lower()
                class_name = elem.get('class', '').lower()
                
                # Check if it's a button
                is_button = 'button' in class_name or 'Button' in class_name
                
                # Check for swipe-related keywords
                has_swipe_keyword = any(keyword in text or keyword in content_desc 
                                      for keyword in ['swipe', 'start', 'begin', 'go'])
                
                if is_button and has_swipe_keyword:
                    # Try to get a locator
                    if resource_id:
                        logger.info(f"Found potential swipe button with resource-id: {resource_id}")
                        return ("id", resource_id)
                    elif content_desc:
                        logger.info(f"Found potential swipe button with content-desc: {content_desc}")
                        return ("accessibility_id", content_desc)
                    elif text:
                        xpath = f"//*[@text='{elem.get('text')}']"
                        logger.info(f"Found potential swipe button with text: {text}")
                        return ("xpath", xpath)
    except Exception as e:
        logger.warning(f"Error analyzing UI hierarchy: {e}")
    
    # Strategy 4: Try to find any large clickable button
    logger.info("Trying to find any large clickable button...")
    try:
        # Get all clickable elements
        driver = page.driver
        elements = driver.find_elements("xpath", "//*[@clickable='true']")
        
        for elem in elements:
            try:
                # Get element bounds
                location = elem.location
                size = elem.size
                area = size['width'] * size['height']
                
                # Prefer larger buttons (likely to be main action button)
                if area > 10000:  # At least 100x100 pixels
                    text = elem.text or elem.get_attribute('content-desc') or ''
                    logger.info(f"Found large clickable element: {text} (area: {area})")
                    
                    # Try to get a locator
                    resource_id = elem.get_attribute('resource-id')
                    if resource_id:
                        return ("id", resource_id)
                    
                    content_desc = elem.get_attribute('content-desc')
                    if content_desc:
                        return ("accessibility_id", content_desc)
                    
                    if text:
                        xpath = f"//*[@text='{text}']"
                        return ("xpath", xpath)
            except:
                continue
    except Exception as e:
        logger.warning(f"Error finding clickable elements: {e}")
    
    return None


def main():
    """Find and click the swipe button in Doubble app."""
    try:
        logger.info("=" * 60)
        logger.info("Finding and Clicking Swipe Button")
        logger.info("=" * 60)
        
        # Initialize driver
        logger.info("Initializing Appium driver...")
        driver = get_driver()
        logger.info("Driver initialized successfully")
        
        # Create base page for interactions
        page = BasePage()
        
        # Wait a moment for everything to settle
        time.sleep(2)
        
        # Make sure we're in the Doubble app
        logger.info("Ensuring Doubble app is open...")
        try:
            driver.activate_app("dk.doubble.dating")
            time.sleep(3)
        except:
            driver.start_activity("dk.doubble.dating", ".MainActivity")
            time.sleep(5)
        
        # Take a screenshot before
        logger.info("Taking screenshot before button search...")
        page.take_screenshot("before_swipe_button_search.png")
        
        # Find the swipe button
        logger.info("=" * 60)
        button_locator = find_swipe_button(page)
        
        if button_locator:
            locator_type, locator_value = button_locator
            logger.info(f"Found swipe button! Locator: {locator_type}={locator_value}")
            logger.info("Clicking the swipe button...")
            
            # Click the button
            page.tap(locator_type, locator_value)
            logger.info("Swipe button clicked successfully!")
            
            # Wait a moment
            time.sleep(2)
            
            # Take a screenshot after
            logger.info("Taking screenshot after button click...")
            page.take_screenshot("after_swipe_button_click.png")
            
            logger.info("=" * 60)
            logger.info("Successfully clicked the swipe button!")
            logger.info("=" * 60)
            
            return 0
        else:
            logger.error("Could not find swipe button!")
            logger.info("Taking screenshot for manual inspection...")
            page.take_screenshot("swipe_button_not_found.png")
            
            # Print UI hierarchy for debugging
            logger.info("Getting UI hierarchy for debugging...")
            try:
                source = driver.page_source
                with open("ui_hierarchy.xml", "w", encoding="utf-8") as f:
                    f.write(source)
                logger.info("UI hierarchy saved to ui_hierarchy.xml")
            except Exception as e:
                logger.warning(f"Could not save UI hierarchy: {e}")
            
            return 1
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        return 1
    finally:
        logger.info("Cleaning up...")
        close_driver()
        logger.info("Done!")


if __name__ == "__main__":
    sys.exit(main())

