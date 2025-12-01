"""
Doubble swipe screen page object.
Handles interactions on the swipe/card screen.
"""

import logging
import time
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional
from .base_page import BasePage

logger = logging.getLogger(__name__)


class DoubbleSwipePage(BasePage):
    """Page object for the swipe/card screen in Doubble app."""
    
    # Cached like button information (set once, reused for speed)
    _cached_like_button_locator = None  # (locator_type, locator_value)
    _cached_like_button_coords = None   # (x, y) center coordinates
    _cached_like_button_element = None  # Cached element reference
    
    # Like button locators - ordered by reliability (most reliable first)
    # FIXED: Excludes navigation buttons - only finds heart button (no text) on swipe screen
    LIKE_BUTTON_LOCATORS = [
        # Priority 1: Heart buttons WITHOUT text (not navigation "Likes" button)
        # XPath that explicitly excludes buttons with text and excludes navigation area
        ("xpath", "//*[@clickable='true' and not(@text) and contains(@content-desc, 'Like') and not(ancestor::*[contains(@class, 'Navigation') or contains(@class, 'BottomNavigation') or contains(@class, 'Tab')])]"),
        ("xpath", "//*[@clickable='true' and not(@text) and contains(@content-desc, 'like') and not(ancestor::*[contains(@class, 'Navigation') or contains(@class, 'BottomNavigation')])]"),
        # Priority 2: ImageButton or ImageView (heart icon) - no text attribute
        ("xpath", "//android.widget.ImageButton[@clickable='true' and not(@text) and (contains(@content-desc, 'Like') or contains(@content-desc, 'like') or contains(@content-desc, 'Heart'))]"),
        ("xpath", "//android.widget.ImageView[@clickable='true' and not(@text) and (contains(@content-desc, 'Like') or contains(@content-desc, 'like') or contains(@content-desc, 'Heart'))]"),
        # Priority 3: Resource IDs for heart/like button on swipe screen
        ("id", "dk.doubble.dating:id/like"),
        ("id", "dk.doubble.dating:id/like_button"),
        ("id", "dk.doubble.dating:id/btn_like"),
        ("id", "dk.doubble.dating:id/heart"),
        ("id", "dk.doubble.dating:id/btn_heart"),
    ]
    
    # Pop-up/dialog close/cancel button locators - expanded list
    POPUP_CLOSE_LOCATORS = [
        # App-specific IDs
        ("id", "dk.doubble.dating:id/close"),
        ("id", "dk.doubble.dating:id/cancel"),
        ("id", "dk.doubble.dating:id/dismiss"),
        ("id", "dk.doubble.dating:id/close_button"),
        ("id", "dk.doubble.dating:id/btn_close"),
        ("id", "dk.doubble.dating:id/btn_cancel"),
        ("id", "dk.doubble.dating:id/btn_dismiss"),
        # Accessibility IDs
        ("accessibility_id", "Close"),
        ("accessibility_id", "Cancel"),
        ("accessibility_id", "Dismiss"),
        ("accessibility_id", "No Thanks"),
        ("accessibility_id", "Not Now"),
        ("accessibility_id", "Later"),
        # Android system dialog buttons
        ("id", "android:id/button2"),  # Negative button (Cancel, No, etc.)
        ("id", "android:id/button1"),  # Positive button (sometimes used for dismiss)
        # Text-based locators
        ("xpath", "//*[contains(@text, 'Close') or contains(@text, 'close')]"),
        ("xpath", "//*[contains(@text, 'Cancel') or contains(@text, 'cancel')]"),
        ("xpath", "//*[contains(@text, 'Dismiss') or contains(@text, 'dismiss')]"),
        ("xpath", "//*[contains(@text, 'No Thanks') or contains(@text, 'No thanks')]"),
        ("xpath", "//*[contains(@text, 'Not Now') or contains(@text, 'Not now')]"),
        ("xpath", "//*[contains(@text, 'Later') or contains(@text, 'later')]"),
        ("xpath", "//*[contains(@text, 'Skip') or contains(@text, 'skip')]"),
        ("xpath", "//*[contains(@text, 'Maybe Later')]"),
        # Content description locators
        ("xpath", "//*[contains(@content-desc, 'Close') or contains(@content-desc, 'close')]"),
        ("xpath", "//*[contains(@content-desc, 'Cancel') or contains(@content-desc, 'cancel')]"),
        ("xpath", "//*[contains(@content-desc, 'Dismiss')]"),
        # Android system buttons
        ("xpath", "//android.widget.Button[@text='Cancel']"),
        ("xpath", "//android.widget.Button[@text='Close']"),
        ("xpath", "//android.widget.Button[@text='No Thanks']"),
        ("xpath", "//android.widget.Button[@text='Not Now']"),
        ("xpath", "//android.widget.ImageButton[@content-desc='Close']"),
        ("xpath", "//android.widget.ImageButton[@content-desc='Dismiss']"),
    ]
    
    # Common pop-up/dialog container classes
    POPUP_CONTAINER_CLASSES = [
        "android.widget.Dialog",
        "android.app.Dialog",
        "androidx.appcompat.app.AlertDialog",
        "com.google.android.material.dialog.MaterialAlertDialogBuilder",
    ]
    
    def find_like_button(self, quiet=False, use_cache=True):
        """
        Find the heart like button on swipe screen (NOT navigation bar button).
        OPTIMIZED: Uses cached button location after first detection for maximum speed.
        
        Args:
            quiet: If True, reduce logging for faster operation
            use_cache: If True, use cached button location (default: True for speed)
        
        Returns:
            tuple: (locator_type, locator_value) or None
        """
        # OPTIMIZED: Try cached button first (instant - no search needed)
        if use_cache and self._cached_like_button_locator:
            locator_type, locator_value = self._cached_like_button_locator
            # Quick verification that cached button still exists (ultra-fast check)
            try:
                if self.is_element_present_silent(locator_type, locator_value, timeout=0.05):
                    if not quiet:
                        logger.debug(f"Using cached like button: {locator_type}={locator_value[:50]}...")
                    return self._cached_like_button_locator
                else:
                    # Cached button no longer exists - clear cache and re-detect
                    if not quiet:
                        logger.debug("Cached like button not found - re-detecting...")
                    self._cached_like_button_locator = None
                    self._cached_like_button_coords = None
                    self._cached_like_button_element = None
            except:
                # Error checking cached button - clear cache and re-detect
                self._cached_like_button_locator = None
                self._cached_like_button_coords = None
                self._cached_like_button_element = None
        
        if not quiet:
            logger.info("Searching for heart like button (not navigation bar)...")
        
        # ULTRA-FAST: Try only 1 locator with minimal timeout (0.05s) - if not found, skip to swipe
        check_method = self.is_element_present_silent if quiet else self.is_element_present
        timeout = 0.05  # ULTRA-FAST: 50ms timeout only
        
        # Try only the FIRST (most reliable) locator - if it fails, skip to swipe immediately
        try:
            locator_type, locator_value = self.LIKE_BUTTON_LOCATORS[0]
            if check_method(locator_type, locator_value, timeout=timeout):
                if not quiet:
                    logger.debug(f"Found heart like button: {locator_type}={locator_value[:50]}...")
                # CACHE the found button for future use (makes subsequent calls instant)
                self._cached_like_button_locator = (locator_type, locator_value)
                # Try to extract and cache coordinates (async - don't wait if it fails)
                try:
                    self._extract_and_cache_button_coordinates(locator_type, locator_value, quiet)
                except:
                    pass  # If coordinate extraction fails, still use locator
                return (locator_type, locator_value)
        except Exception as e:
            # Handle UiAutomator2 crashes
            error_str = str(e).lower()
            if "instrumentation process is not running" in error_str or "crashed" in error_str:
                if not quiet:
                    logger.warning("UiAutomator2 server crashed during button search")
                raise  # Re-raise to trigger reconnection
        
        # ULTRA-FAST: Skip all other locators and XML analysis - go straight to swipe gesture
        # XML analysis takes 30+ seconds - not worth it. Swipe gesture is faster.
        if not quiet:
            logger.debug("Like button not found in 50ms - using swipe gesture instead")
        return None  # Return None to trigger swipe gesture immediately
    
    def _extract_and_cache_button_coordinates(self, locator_type, locator_value, quiet=False):
        """
        Extract button coordinates from XML and cache them for direct tapping.
        This makes subsequent clicks instant (no element search needed).
        """
        try:
            # Get element to extract its bounds/coordinates
            element = self.find_element(locator_type, locator_value, timeout=0.3)
            location = element.location
            size = element.size
            # Calculate center coordinates
            center_x = location['x'] + size['width'] // 2
            center_y = location['y'] + size['height'] // 2
            self._cached_like_button_coords = (center_x, center_y)
            self._cached_like_button_element = element  # Cache element reference
            if not quiet:
                logger.debug(f"Cached like button coordinates: ({center_x}, {center_y})")
        except:
            pass  # If extraction fails, we still have the locator cached
    
    def _find_like_button_from_xml(self, quiet=False):
        """
        Find like button by analyzing XML page source once, then cache coordinates.
        This is efficient because we only do it once, then reuse cached coordinates.
        """
        try:
            page_source = self.driver.page_source
            if not page_source:
                return None
            
            root = ET.fromstring(page_source)
            
            # Get screen dimensions for filtering
            try:
                window_size = self.driver.get_window_size()
                screen_height = window_size['height']
            except:
                screen_height = 1920  # Default fallback
            
            # Find heart buttons (no text) in swipe area
            best_button = None
            best_priority = 0
            
            for elem in root.iter():
                clickable = elem.get('clickable', 'false') == 'true'
                content_desc = (elem.get('content-desc') or '').lower()
                text = (elem.get('text') or '').strip()
                resource_id = elem.get('resource-id', '')
                bounds = elem.get('bounds', '')
                
                # Heart button: clickable, has like/heart content-desc, NO text, has resource ID
                is_heart_button = (
                    clickable and 
                    ('like' in content_desc or 'heart' in content_desc) and
                    not text and  # NO TEXT (heart buttons don't have text)
                    resource_id   # Has resource ID
                )
                
                if is_heart_button:
                    # Check position - exclude navigation bars
                    if bounds:
                        try:
                            bounds_clean = bounds.replace('[', '').replace(']', ',')
                            coords = [int(c.strip()) for c in bounds_clean.split(',') if c.strip().isdigit()]
                            if len(coords) >= 4:
                                y_center = (coords[1] + coords[3]) / 2
                                x_center = (coords[0] + coords[2]) / 2
                                # Exclude top/bottom 15% (navigation areas)
                                is_in_swipe_area = screen_height * 0.15 < y_center < screen_height * 0.85
                                
                                if is_in_swipe_area:
                                    priority = 10 if not text else 0  # Heart buttons (no text) get priority
                                    # Cache coordinates directly from XML parsing
                                    self._cached_like_button_coords = (int(x_center), int(y_center))
                                    
                                    if priority > best_priority:
                                        best_priority = priority
                                        if resource_id:
                                            best_button = ("id", resource_id)
                                            self._cached_like_button_locator = best_button
                                        elif content_desc:
                                            best_button = ("accessibility_id", elem.get('content-desc'))
                                            self._cached_like_button_locator = best_button
                        except:
                            pass
            
            if best_button:
                if not quiet:
                    logger.info(f"Found and cached like button from XML: {best_button[0]}={best_button[1][:50]}...")
                return best_button
        except Exception as e:
            if not quiet:
                logger.debug(f"XML analysis failed: {e}")
        
        return None
    
    def clear_like_button_cache(self):
        """
        Clear the cached like button information.
        Call this when screen changes or button location might have moved.
        """
        self._cached_like_button_locator = None
        self._cached_like_button_coords = None
        self._cached_like_button_element = None
        logger.debug("Cleared like button cache")
    
    def click_like_button(self, quiet=False):
        """
        Click the like button.
        OPTIMIZED: Uses cached coordinates for direct tapping (instant - no search needed).
        
        Args:
            quiet: If True, reduce logging for faster operation
        
        Returns:
            bool: True if button was found and clicked, False otherwise
        """
        # ULTRA-FAST PATH: If we have cached coordinates, tap directly (no search at all!)
        if self._cached_like_button_coords:
            try:
                x, y = self._cached_like_button_coords
                if not quiet:
                    logger.debug(f"Tapping cached like button at coordinates: ({x}, {y})")
                self.driver.tap([(x, y)], 100)  # Direct tap on coordinates - instant!
                time.sleep(0.05)  # Minimal wait
                return True
            except Exception as e:
                # Cached coordinates failed - clear cache and fall back to locator search
                if not quiet:
                    logger.debug(f"Cached coordinates failed, re-detecting: {e}")
                self._cached_like_button_coords = None
                self._cached_like_button_element = None
        
        # FALLBACK: Use locator-based search (still cached after first find)
        button_locator = self.find_like_button(quiet=quiet, use_cache=True)
        
        if button_locator:
            locator_type, locator_value = button_locator
            if not quiet:
                logger.debug(f"Clicking like button: {locator_type}={locator_value[:50]}...")
            
            # Try to use cached element if available (faster than finding again)
            if self._cached_like_button_element:
                try:
                    self._cached_like_button_element.click()
                    time.sleep(0.05)  # Minimal wait
                    return True
                except:
                    # Cached element stale - clear and use tap method
                    self._cached_like_button_element = None
            
            # Use standard tap method (which will cache for next time)
            try:
                element = self.find_element(locator_type, locator_value, timeout=0.3)
                element.click()
                # Extract and cache coordinates while we have the element
                try:
                    location = element.location
                    size = element.size
                    center_x = location['x'] + size['width'] // 2
                    center_y = location['y'] + size['height'] // 2
                    self._cached_like_button_coords = (center_x, center_y)
                    self._cached_like_button_element = element  # Cache element reference
                    if not quiet:
                        logger.debug(f"Extracted and cached coordinates: ({center_x}, {center_y})")
                except:
                    pass  # If coordinate extraction fails, that's okay
                time.sleep(0.05)  # ULTRA-FAST: Reduced from 0.1s to 0.05s
                return True
            except Exception as e:
                if not quiet:
                    logger.warning(f"Failed to click like button: {e}")
                return False
        else:
            if not quiet:
                logger.debug("Like button not found - cannot click")
            return False
    
    def analyze_ui_hierarchy_for_popups(self) -> List[Tuple[str, str, str]]:
        """
        Analyze the UI hierarchy to find pop-up elements dynamically.
        
        Returns:
            List of tuples: [(locator_type, locator_value, element_info), ...]
        """
        popup_elements = []
        
        try:
            # Get the page source as XML
            page_source = self.driver.page_source
            if not page_source:
                return popup_elements
            
            root = ET.fromstring(page_source)
            
            # Keywords that indicate pop-up/dialog buttons
            dismiss_keywords = [
                'cancel', 'close', 'dismiss', 'no thanks', 'not now', 
                'later', 'skip', 'maybe later', 'decline', 'not interested'
            ]
            
            # Find all clickable elements
            for elem in root.iter():
                # Check for dialog containers
                class_name = elem.get('class', '').lower()
                if any(popup_class.lower() in class_name for popup_class in self.POPUP_CONTAINER_CLASSES):
                    logger.info(f"Found pop-up container: {class_name}")
                    # Look for buttons inside this container
                    for button in elem.findall(".//*[@clickable='true']"):
                        text = (button.get('text') or '').lower()
                        content_desc = (button.get('content-desc') or '').lower()
                        resource_id = button.get('resource-id', '')
                        
                        # Check if this looks like a dismiss button
                        if any(keyword in text or keyword in content_desc for keyword in dismiss_keywords):
                            if resource_id:
                                popup_elements.append(("id", resource_id, f"text='{button.get('text')}'"))
                            elif content_desc:
                                popup_elements.append(("accessibility_id", button.get('content-desc'), f"content-desc='{content_desc}'"))
                            elif text:
                                popup_elements.append(("xpath", f"//*[@text='{button.get('text')}']", f"text='{text}'"))
                
                # Check individual clickable elements for dismiss keywords
                if elem.get('clickable', '').lower() == 'true':
                    text = (elem.get('text') or '').lower()
                    content_desc = (elem.get('content-desc') or '').lower()
                    resource_id = elem.get('resource-id', '')
                    
                    # Check if text or content-desc contains dismiss keywords
                    if any(keyword in text or keyword in content_desc for keyword in dismiss_keywords):
                        if resource_id and resource_id not in [e[1] for e in popup_elements]:
                            popup_elements.append(("id", resource_id, f"text='{elem.get('text')}' content-desc='{content_desc}'"))
                        elif content_desc and content_desc not in [e[1] for e in popup_elements if e[0] == 'accessibility_id']:
                            popup_elements.append(("accessibility_id", elem.get('content-desc'), f"content-desc='{content_desc}'"))
                        elif text and text not in [e[2] for e in popup_elements]:
                            popup_elements.append(("xpath", f"//*[@text='{elem.get('text')}']", f"text='{text}'"))
                
                # Check for Android system dialog buttons
                if elem.get('resource-id') == 'android:id/button2':  # Negative button
                    popup_elements.append(("id", "android:id/button2", "Android system negative button"))
                elif elem.get('resource-id') == 'android:id/button1' and 'cancel' in (elem.get('text') or '').lower():
                    popup_elements.append(("id", "android:id/button1", f"Android system button: {elem.get('text')}"))
        
        except Exception as e:
            logger.warning(f"Error analyzing UI hierarchy for pop-ups: {e}")
        
        return popup_elements
    
    def handle_popups(self, max_attempts=5):
        """
        Handle any pop-ups that appear by dismissing/canceling them.
        Uses both predefined locators and dynamic UI hierarchy analysis.
        
        Args:
            max_attempts: Maximum number of pop-ups to dismiss
        """
        logger.info("=" * 60)
        logger.info("Analyzing screen for pop-ups...")
        logger.info("=" * 60)
        
        dismissed_count = 0
        
        for attempt in range(max_attempts):
            popup_found = False
            popup_info = None
            
            # First, try dynamic analysis of UI hierarchy
            logger.info(f"Attempt {attempt + 1}: Analyzing UI hierarchy for pop-ups...")
            dynamic_popups = self.analyze_ui_hierarchy_for_popups()
            
            if dynamic_popups:
                logger.info(f"Found {len(dynamic_popups)} potential pop-up elements via UI analysis:")
                for loc_type, loc_value, info in dynamic_popups:
                    logger.info(f"  - {loc_type}={loc_value} ({info})")
                
                # Try to click the first found pop-up element
                for loc_type, loc_value, info in dynamic_popups:
                    if self.is_element_present(loc_type, loc_value, timeout=1):
                        logger.info(f"Found active pop-up: {loc_type}={loc_value} ({info})")
                        try:
                            self.tap(loc_type, loc_value)
                            logger.info(f"[OK] Dismissed pop-up: {info}")
                            popup_found = True
                            popup_info = info
                            dismissed_count += 1
                            time.sleep(1)  # Wait for pop-up to disappear
                            break
                        except Exception as e:
                            logger.warning(f"Error clicking pop-up element: {e}")
            
            # If dynamic analysis didn't find anything, try predefined locators
            if not popup_found:
                logger.info(f"Attempt {attempt + 1}: Trying predefined pop-up locators...")
                for locator_type, locator_value in self.POPUP_CLOSE_LOCATORS:
                    if self.is_element_present(locator_type, locator_value, timeout=1):
                        logger.info(f"Found pop-up close button: {locator_type}={locator_value}")
                        try:
                            self.tap(locator_type, locator_value)
                            logger.info(f"[OK] Dismissed pop-up: {locator_type}={locator_value}")
                            popup_found = True
                            popup_info = f"{locator_type}={locator_value}"
                            dismissed_count += 1
                            time.sleep(1)  # Wait for pop-up to disappear
                            break
                        except Exception as e:
                            logger.warning(f"Error dismissing pop-up: {e}")
            
            # If still no pop-up found, try pressing back button as last resort
            if not popup_found:
                # Check if we're in a dialog by looking for dialog indicators
                try:
                    page_source = self.driver.page_source.lower()
                    if any(indicator in page_source for indicator in ['dialog', 'modal', 'popup', 'overlay']):
                        logger.info("Detected dialog-like content, trying back button...")
                        self.press_back()
                        time.sleep(1)
                        dismissed_count += 1
                        popup_found = True
                        popup_info = "Back button"
                except Exception:
                    pass
            
            # If no pop-up found in this attempt, we're done
            if not popup_found:
                break
            
            # Log what was dismissed
            if popup_info:
                logger.info(f"Successfully handled pop-up: {popup_info}")
        
        # Summary
        logger.info("=" * 60)
        if dismissed_count > 0:
            logger.info(f"[OK] Pop-up analysis complete: Dismissed {dismissed_count} pop-up(s)")
        else:
            logger.info("[OK] No pop-ups detected on screen")
        logger.info("=" * 60)
        
        return dismissed_count
    
    def handle_popups_quiet(self, max_attempts=2):
        """
        Handle pop-ups silently (no error logging for faster like automation).
        OPTIMIZED: Ultra-fast pop-up detection with minimal timeouts.
        
        Args:
            max_attempts: Maximum number of pop-ups to dismiss
            
        Returns:
            int: Number of pop-ups dismissed
        """
        dismissed_count = 0
        
        for attempt in range(max_attempts):
            popup_found = False
            
            # OPTIMIZED: Try only top 5 most common locators with reduced timeout
            for locator_type, locator_value in self.POPUP_CLOSE_LOCATORS[:5]:  # Only check first 5
                try:
                    if self.is_element_present_silent(locator_type, locator_value, timeout=0.2):  # Reduced timeout
                        # Silently tap without logging
                        try:
                            element = self.find_element(locator_type, locator_value, timeout=0.3)  # Reduced timeout
                            element.click()
                            dismissed_count += 1
                            popup_found = True
                            time.sleep(0.2)  # Reduced wait time
                            break
                        except:
                            pass
                except Exception:
                    continue
            
            # If no pop-up found, we're done (no need to try more)
            if not popup_found:
                break
        
        return dismissed_count

