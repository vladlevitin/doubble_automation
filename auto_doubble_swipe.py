import sys
import os
import time
import signal
import socket
import subprocess
import shutil
from pathlib import Path
from urllib3.exceptions import NewConnectionError, MaxRetryError
from requests.exceptions import ConnectionError as RequestsConnectionError
from selenium.common.exceptions import WebDriverException

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

# Global flag for graceful shutdown
running = True

# Connection error types to catch
CONNECTION_ERRORS = (
    NewConnectionError,
    MaxRetryError,
    RequestsConnectionError,
    WebDriverException,
    ConnectionError,
)

# UiAutomator2 crash error messages to detect
UIAUTOMATOR2_CRASH_INDICATORS = [
    "instrumentation process is not running",
    "probably crashed",
    "uiautomator2",
    "proxyCommand",
]

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    logger.info("\nReceived interrupt signal. Stopping gracefully...")
    running = False
    close_driver()
    stop_appium_server()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def is_appium_server_down(error) -> bool:
    """
    Check if the error indicates Appium server is completely down (not just UiAutomator2 crash).
    
    Args:
        error: Exception or error message
    
    Returns:
        bool: True if Appium server appears to be down
    """
    error_str = str(error).lower()
    # Check for connection refused errors (server not running)
    if "connection refused" in error_str or "actively refused" in error_str or "10061" in error_str:
        return True
    return False


def run_powershell_command(command: str, timeout: int = 10) -> tuple:
    """
    Run a PowerShell command and return the result.
    
    Args:
        command: PowerShell command to execute
        timeout: Timeout in seconds
        
    Returns:
        tuple: (success: bool, stdout: str, stderr: str)
    """
    try:
        # Use -NoProfile -NonInteractive for faster startup
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        return (result.returncode == 0, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        logger.warning(f"PowerShell command timed out after {timeout} seconds")
        return (False, "", f"Timeout after {timeout} seconds")
    except Exception as e:
        logger.warning(f"Failed to run PowerShell command: {e}")
        return (False, "", str(e))


def check_appium_server_reachable() -> bool:
    """
    Quick check if Appium server is reachable on port 4723.
    
    Returns:
        bool: True if server is reachable, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # 1 second timeout
        result = sock.connect_ex(('localhost', 4723))
        sock.close()
        return result == 0
    except:
        return False


# Global variable to store Appium process
_appium_process = None


def start_appium_server() -> bool:
    """
    Start Appium server automatically if it's not running.
    
    Returns:
        bool: True if server started successfully, False otherwise
    """
    global _appium_process
    
    try:
        # Check if Appium is already running
        if check_appium_server_reachable():
            logger.info("[OK] Appium server is already running")
            return True
        
        # Check if Appium command is available
        appium_cmd = shutil.which("appium")
        if not appium_cmd:
            logger.warning("Appium command not found in PATH. Trying PowerShell to find Appium...")
            # Try to find Appium using PowerShell (npm global packages)
            ps_cmd = 'Get-Command appium -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source'
            success, output, _ = run_powershell_command(ps_cmd, timeout=5)
            if success and output.strip():
                appium_cmd = output.strip()
                logger.info(f"Found Appium via PowerShell: {appium_cmd}")
            else:
                logger.error("Appium command not found. Please install Appium:")
                logger.error("  npm install -g appium")
                logger.error("  or install via: npm install -g @appium/appium")
                return False
        
        logger.info("=" * 60)
        logger.info("Starting Appium server automatically...")
        logger.info("=" * 60)
        logger.info("")
        
        # Start Appium server in background
        # Redirect stdout/stderr to pipes so it runs in background
        logger.info(f"Starting Appium process: {appium_cmd}")
        _appium_process = subprocess.Popen(
            [appium_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        logger.info("Waiting for Appium server to start (this may take 5 to 19 seconds)...")
        
        # Wait for Appium to be ready (max 30 seconds)
        max_wait = 30
        waited = 0
        check_interval = 2
        
        while waited < max_wait:
            time.sleep(check_interval)
            waited += check_interval
            
            # Check if process is still running
            poll_result = _appium_process.poll()
            if poll_result is not None:
                # Process terminated
                stdout, stderr = _appium_process.communicate()
                logger.error("Appium server process terminated unexpectedly")
                logger.error(f"Exit code: {poll_result}")
                if stderr:
                    error_msg = stderr.decode('utf-8', errors='ignore')
                    logger.error(f"Error output: {error_msg[:1000]}")
                if stdout:
                    output_msg = stdout.decode('utf-8', errors='ignore')
                    logger.error(f"Standard output: {output_msg[:1000]}")
                _appium_process = None
                return False
            
            # Check if server is reachable
            if check_appium_server_reachable():
                # Double-check: wait a moment and verify again to ensure it's stable
                time.sleep(1)
                if check_appium_server_reachable():
                    logger.info(f"[OK] Appium server started successfully! (took {waited} seconds)")
                    logger.info("")
                    return True
                else:
                    logger.debug("Server was reachable but became unreachable - continuing to wait...")
            
            if waited % 6 == 0:  # Log every 6 seconds
                logger.info(f"  Still waiting... ({waited}/{max_wait} seconds)")
                # Log that process is still running
                if _appium_process.poll() is None:
                    logger.debug("  Appium process is still running...")
        
        # Timeout - try PowerShell as fallback
        logger.warning(f"Timeout: Appium server did not start within {max_wait} seconds using subprocess")
        logger.info("Attempting to start Appium using PowerShell as fallback...")
        
        # Try starting Appium using PowerShell Start-Job (more reliable on Windows)
        ps_start_cmd = f'Start-Job -ScriptBlock {{ appium }} | Out-Null; Start-Sleep -Seconds 3; $test = Test-NetConnection -ComputerName localhost -Port 4723 -WarningAction SilentlyContinue -InformationLevel Quiet; if ($test) {{ Write-Output "READY" }} else {{ Write-Output "NOT_READY" }}'
        success, output, _ = run_powershell_command(ps_start_cmd, timeout=10)
        
        if success and "READY" in output:
            logger.info("[OK] Appium server started successfully using PowerShell!")
            logger.info("Note: Appium is running in a PowerShell background job")
        return True
        
        logger.error("Appium server failed to start using both methods")
        logger.error("Please start Appium manually or check for errors")
        if _appium_process:
            _appium_process.terminate()
            _appium_process = None
        return False
        
    except Exception as e:
        logger.error(f"Error starting Appium server: {e}")
        if _appium_process:
            try:
                _appium_process.terminate()
            except:
                pass
            _appium_process = None
        return False


def stop_appium_server():
    """Stop the Appium server if it was started by this script."""
    global _appium_process
    
    if _appium_process is not None:
        try:
            logger.info("Stopping Appium server...")
            _appium_process.terminate()
            # Wait a bit for graceful shutdown
            try:
                _appium_process.wait(timeout=5)
            except Exception as timeout_error:
                if type(timeout_error).__name__ == 'TimeoutExpired':
                    # Force kill if it doesn't terminate
                    _appium_process.kill()
                    _appium_process.wait()
            logger.info("[OK] Appium server stopped")
        except Exception as e:
            logger.warning(f"Error stopping Appium server: {e}")
        finally:
            _appium_process = None


def is_uiautomator2_crash_error(error) -> bool:
    """
    Check if the error indicates UiAutomator2 server crash.
    
    Args:
        error: Exception or error message
        
    Returns:
        bool: True if error indicates UiAutomator2 crash
    """
    error_str = str(error).lower()
    return any(indicator.lower() in error_str for indicator in UIAUTOMATOR2_CRASH_INDICATORS)


def check_connection_health(driver) -> bool:
    """
    Check if the Appium driver connection is still alive.
    Also detects UiAutomator2 crashes and Appium server being down.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    # OPTIMIZED: Quick check if Appium server is reachable first (fastest check)
    if not check_appium_server_reachable():
        logger.warning("Appium server is not reachable on port 4723")
        return False
    
    try:
        # Try a simple operation that requires server connection
        driver.current_activity
        return True
    except CONNECTION_ERRORS as e:
        if is_appium_server_down(e):
            logger.warning("Appium server appears to be down (connection refused)")
        elif is_uiautomator2_crash_error(e):
            logger.warning("UiAutomator2 server crash detected - instrumentation process not running")
        else:
            logger.warning("Connection health check failed - Appium server appears disconnected")
        return False
    except Exception as e:
        # Check if it's a UiAutomator2 crash even if not in CONNECTION_ERRORS
        if is_uiautomator2_crash_error(e):
            logger.warning("UiAutomator2 server crash detected in health check")
            return False
        if is_appium_server_down(e):
            logger.warning("Appium server appears to be down")
            return False
        # Other exceptions might not be connection-related
        logger.debug(f"Connection check returned unexpected error: {e}")
        return True  # Assume connection is fine if it's not a connection error


def reconnect_driver() -> bool:
    """
    Attempt to reconnect to Appium by closing old driver and creating a new one.
    Handles UiAutomator2 crashes by waiting for server recovery.
    Also attempts to reactivate the Doubble app.
    
    Returns:
        bool: True if reconnection succeeded, False otherwise
    """
    logger.warning("=" * 60)
    logger.warning("Attempting to reconnect to Appium server...")
    logger.warning("=" * 60)
    
    try:
        # Close old driver
        try:
            close_driver()
        except:
            pass  # Ignore errors when closing dead connection
        
        # Wait longer if UiAutomator2 crashed (needs time to recover)
        logger.info("Waiting for UiAutomator2 server to recover...")
        time.sleep(5)  # Increased wait time for UiAutomator2 recovery
        
        # Try to create new driver (this will restart UiAutomator2 session)
        logger.info("Creating new driver connection...")
        try:
            driver = get_driver()
        except Exception as e:
            logger.error(f"[ERROR] Failed to create new driver: {e}")
            logger.error("UiAutomator2 server may need manual restart")
            return False
        
        # OPTIMIZED: Check if Appium server is reachable first (fastest check)
        if not check_appium_server_reachable():
            logger.error("[ERROR] Appium server is not reachable on port 4723")
            logger.error("Please ensure Appium server is running: appium")
            return False
        
        # Verify connection works (with retries for UiAutomator2 startup)
        max_health_checks = 2  # Reduced from 3 to 2 for faster failure
        for check_attempt in range(max_health_checks):
            if check_connection_health(driver):
                break
            if check_attempt < max_health_checks - 1:
                logger.info(f"Health check failed, waiting for UiAutomator2 to start... (attempt {check_attempt + 1}/{max_health_checks})")
                time.sleep(2)  # Reduced from 3s to 2s
            else:
                logger.error("[ERROR] Reconnection failed - connection still not healthy after retries")
                return False
        
        # Try to reactivate the app
        logger.info("Attempting to reactivate Doubble app...")
        try:
            driver.activate_app("dk.doubble.dating")
            logger.info("[OK] App reactivated")
            time.sleep(2)  # Reduced wait time
        except Exception as e:
            logger.warning(f"Could not reactivate app automatically: {e}")
            logger.info("App may still be open on the device. Continuing...")
        
        logger.info("[OK] Successfully reconnected to Appium!")
        return True
    except Exception as e:
        error_msg = str(e)
        if is_uiautomator2_crash_error(e):
            logger.error(f"[ERROR] UiAutomator2 crash detected during reconnection: {error_msg}")
            logger.error("The UiAutomator2 server may need to be restarted manually.")
            logger.error("Try restarting the Appium server or the emulator.")
        else:
            logger.error(f"[ERROR] Failed to reconnect: {e}")
            logger.error("Please check if Appium server is running and restart if needed.")
        return False


def retry_with_reconnect(func, *args, max_retries=2, **kwargs):
    """
    Execute a function with automatic reconnection on connection errors.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func or None if all retries failed
    """
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except CONNECTION_ERRORS as e:
            if attempt < max_retries:
                error_msg = str(e)
                if is_uiautomator2_crash_error(e):
                    logger.warning(f"UiAutomator2 crash detected (attempt {attempt + 1}/{max_retries + 1})")
                else:
                    logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries + 1}): {type(e).__name__}")
                
                # Try to reconnect
                if reconnect_driver():
                    logger.info("Retrying operation after reconnection...")
                    # Update driver reference in page objects
                    from drivers import get_driver
                    driver = get_driver()
                    # Note: Page objects will get new driver on next call
                    time.sleep(2)  # Wait a bit longer after reconnection
                    continue
                else:
                    logger.error("Reconnection failed. Cannot retry.")
                    return None
            else:
                if is_uiautomator2_crash_error(e):
                    logger.error(f"Max retries reached. UiAutomator2 server crash: {e}")
                else:
                    logger.error(f"Max retries reached. Connection error: {e}")
                return None
        except Exception as e:
            # Non-connection errors - just raise
            raise
    
    return None


def ensure_on_swipe_screen(page: BasePage, screen_detector: DoubbleScreenDetector, swipe_page: DoubbleSwipePage) -> bool:
    """
    Ensure we're on the swipe screen. Navigate there if needed.
    Uses multiple strategies to get to swipe screen.
    
    Returns:
        bool: True if successfully on swipe screen, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Navigating to swipe screen...")
    logger.info("=" * 60)
    
    # Handle any pop-ups first (quiet mode)
    dismissed = swipe_page.handle_popups_quiet()
    if dismissed > 0:
        logger.info(f"[!] Dismissed {dismissed} pop-up(s)")
    
    # OPTIMIZED: Ultra-fast check first - skip if already on swipe
    try:
        if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.1):
            logger.info("[FAST] Like button found - already on swipe screen!")
            return True
    except:
        pass
    
    # OPTIMIZED: Removed initial wait - not needed
    
    # Try up to 2 attempts (reduced from 3 for speed)
    for attempt in range(1, 3):
        logger.info(f"Navigation attempt {attempt}/2...")
        
        # OPTIMIZED: Ultra-fast like button check first (faster than full screen detection)
        try:
            if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.1):
                logger.info("[OK] Like button found - we're on swipe screen!")
                return True
        except:
            pass
        
        # OPTIMIZED: Skip slow screen detection - just try navigation directly
        # Screen detection already done in main() - we know we need to navigate
        current_screen = "home"  # Assume home if we got here
        
        # If on login screen, we can't proceed
        if current_screen == "login":
            logger.error("On LOGIN screen - user needs to log in manually first!")
            logger.error("Please log in to the app, then run this script again.")
            return False
        
        # If already on swipe screen, we're done
        if current_screen == "swipe":
            logger.info("[OK] Verified - we're on swipe screen!")
            return True
        
        # Always try to navigate to swipe screen if not verified
        if current_screen in ["home", "unknown"]:
            logger.info(f"On {current_screen.upper()} screen - navigating to swipe screen...")
            
            # Strategy 1: FAST - Try direct swipe button locators (no slow analysis)
            swipe_button_locators = [
                ("xpath", "//*[contains(@content-desc, 'Swipe') or contains(@text, 'Swipe')]"),
                ("xpath", "//*[contains(@content-desc, 'swipe') or contains(@text, 'swipe')]"),
                ("accessibility_id", "Swipe"),
                ("accessibility_id", "swipe"),
                ("id", "dk.doubble.dating:id/swipe"),
                ("id", "dk.doubble.dating:id/swipe_button"),
                ("id", "dk.doubble.dating:id/btn_swipe"),
            ]
            
            found_swipe_button = False
            for locator_type, locator_value in swipe_button_locators:
                try:
                    if page.is_element_present_silent(locator_type, locator_value, timeout=0.2):
                        logger.info(f"✓ Found swipe button! Clicking: {locator_type}={locator_value[:50]}...")
                        page.tap(locator_type, locator_value)
                        found_swipe_button = True
                        time.sleep(1.5)  # Reduced wait time
                        
                        # OPTIMIZED: Ultra-fast like button check (faster than screen detection)
                        try:
                            if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.3):
                                logger.info("[OK] Successfully navigated to swipe screen!")
                                return True
                        except:
                            pass
                        break
                except Exception as e:
                    # Skip UiAutomator2 crashes - will be handled by reconnection
                    error_str = str(e).lower()
                    if "instrumentation process is not running" in error_str or "crashed" in error_str:
                        raise  # Re-raise to trigger reconnection
                    continue
            
            if not found_swipe_button:
                logger.debug("Could not find swipe button with direct locators - trying alternatives")
            
            # Strategy 2: Try tapping on swipe-related UI elements (already done above, skip)
            # This is now redundant - removed for speed
            
            # Strategy 3: Try swiping gestures (sometimes we're already on swipe but not detected)
            if attempt >= 2:
                logger.info("Trying swipe gesture as last resort...")
                try:
                    # Try swiping right (like gesture) - if we're on swipe, this will work
                    page.swipe_right()
                    time.sleep(0.8)  # Reduced wait time
                    
                    # Quick check - faster than full screen detection
                    try:
                        if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.3):
                            logger.info("[OK] Found swipe screen via swipe gesture!")
                            return True
                    except:
                        pass
                except Exception as e:
                    logger.debug(f"Swipe gesture failed: {e}")
        
        # OPTIMIZED: Reduced wait time before next attempt
        if attempt < 2:
            time.sleep(0.3)  # Reduced from 0.5s to 0.3s
    
    # OPTIMIZED: Ultra-fast final check - just check like button (faster than screen detection)
    logger.info("Final check for swipe screen...")
    try:
        if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.3):
            logger.info("[OK] Found swipe screen on final check!")
            return True
    except:
        pass
    
    logger.warning("=" * 60)
    logger.warning("Could not navigate to swipe screen automatically.")
    logger.warning("Please manually navigate to the swipe screen in the app.")
    logger.warning("The script will attempt to continue anyway...")
    logger.warning("=" * 60)
    
    # Don't fail completely - let it try to continue
    return False


def swipe_and_like_loop(swipe_page: DoubbleSwipePage, page: BasePage, max_iterations: int = None):
    """
    Continuously like profiles by clicking the like button.
    Saves page source after each action for debugging/identification.
    Includes automatic connection recovery on Appium disconnections.
    
    Args:
        swipe_page: DoubbleSwipePage instance
        page: BasePage instance
        max_iterations: Maximum number of iterations (None for infinite)
    """
    iteration = 0
    likes_count = 0
    consecutive_connection_errors = 0
    max_consecutive_errors = 5
    
    # ULTRA-FAST: Minimal logging for speed
    logger.info("Starting continuous like automation...")
    logger.info("Press Ctrl+C to stop")
    
    # OPTIMIZED: Skip initial page source save for speed
    # Save initial page source to know starting state - DISABLED for speed
    # try:
    #     page.save_page_source("initial_state")
    # except CONNECTION_ERRORS:
    #     logger.warning("Could not save initial page source - connection issue")
    #     if not reconnect_driver():
    #         logger.error("Cannot continue - connection failed")
    #         return
    
    while running:
        iteration += 1
        
        if max_iterations and iteration > max_iterations:
            logger.info(f"Reached maximum iterations ({max_iterations}). Stopping.")
            break
        
        # Periodic connection health check (every 10 iterations)
        if iteration % 10 == 0:
            if not check_connection_health(page.driver):
                logger.warning("Periodic health check failed - attempting reconnection...")
                if reconnect_driver():
                    # Update page objects with new driver
                    from drivers import get_driver
                    new_driver = get_driver()
                    page.driver = new_driver
                    swipe_page.driver = new_driver
                    # Clear cache when reconnecting (old session elements won't work)
                    swipe_page.clear_like_button_cache()
                    consecutive_connection_errors = 0
                    logger.info("Page objects updated with new driver connection")
                else:
                    consecutive_connection_errors += 1
                    if consecutive_connection_errors >= max_consecutive_errors:
                        logger.error(f"Too many consecutive connection errors ({consecutive_connection_errors}). Stopping.")
                        break
        
        logger.info(f"--- Like #{iteration} ---")
        
        try:
            # OPTIMIZED: Check pop-ups less frequently (every 20 iterations) to avoid pauses
            # This prevents the pause on iteration 5
            if iteration % 20 == 0:
                try:
                    dismissed = swipe_page.handle_popups_quiet()
                    if dismissed > 0:
                        logger.info(f"[!] Dismissed {dismissed} pop-up(s)")
                except Exception as popup_error:
                    # Silently continue - don't log errors for speed
                    pass
            # Removed page source save for speed
            
            # ULTRA-FAST: Skip pre-emptive server check - just try to swipe and handle errors if they occur
            # This eliminates unnecessary delays when server is working fine
            
            # ULTRA-FAST: Skip like button search entirely - just use swipe gesture directly
            # Swipe gesture is faster and more reliable than searching for like button
            try:
                page.swipe_right()
                likes_count += 1
                logger.info(f"✓ Swiped right (liked) #{likes_count} (attempt #{iteration})")
                consecutive_connection_errors = 0  # Reset on success
                
                time.sleep(0.05)  # ULTRA-FAST: Minimal wait after swipe (reduced from 0.15s)
            except CONNECTION_ERRORS as e:
                error_str = str(e).lower()
                # OPTIMIZED: Fail fast if Appium server is clearly down
                if is_appium_server_down(e):
                    logger.warning("Appium server is down - attempting reconnection...")
                else:
                    logger.warning(f"Connection error during swipe: {e}")
                
                consecutive_connection_errors += 1
                if consecutive_connection_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive connection errors. Stopping.")
                    break
                
                # Try to reconnect
                if reconnect_driver():
                    from drivers import get_driver
                    new_driver = get_driver()
                    page.driver = new_driver
                    swipe_page.driver = new_driver
                    # Clear cache when reconnecting
                    swipe_page.clear_like_button_cache()
                    consecutive_connection_errors = 0
                    time.sleep(0.5)  # Reduced wait time
                    continue
                else:
                    time.sleep(1)  # Reduced wait time
                    continue
            except Exception as e:
                error_str = str(e).lower()
                logger.warning(f"Error swiping right on iteration #{iteration}: {e}")
                # Check if it's a timeout or hang issue
                if "timeout" in error_str or "timed out" in error_str:
                    logger.warning(f"Timeout detected - this might indicate Appium connection issue")
                # Always continue the loop - don't let one failed swipe stop everything
                consecutive_connection_errors += 1
                if consecutive_connection_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors. Stopping.")
                    break
                time.sleep(0.2)  # Minimal wait on error
                continue  # Continue to next iteration
        
        except CONNECTION_ERRORS as e:
            error_str = str(e).lower()
            # OPTIMIZED: Fail fast if Appium server is clearly down
            if is_appium_server_down(e):
                logger.warning("Appium server is down - attempting reconnection...")
            else:
                logger.warning(f"Connection error in main loop: {e}")
            
            consecutive_connection_errors += 1
            if consecutive_connection_errors >= max_consecutive_errors:
                logger.error("Too many consecutive connection errors. Stopping.")
                break
            
            # Try to reconnect
            if reconnect_driver():
                from drivers import get_driver
                new_driver = get_driver()
                page.driver = new_driver
                swipe_page.driver = new_driver
                # Clear cache when reconnecting
                swipe_page.clear_like_button_cache()
                time.sleep(1)  # Reduced wait time
                continue
            else:
                logger.warning("Reconnection failed. Waiting before retry...")
                time.sleep(2)  # Reduced wait time
                continue
        
        # ULTRA-FAST: No delay between iterations for maximum speed
        # Removed sleep entirely for fastest possible swiping
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Swipe automation completed")
    logger.info(f"Total likes: {likes_count}")
    logger.info(f"Total iterations: {iteration}")
    logger.info("=" * 60)


def send_message_in_chat(page: BasePage, message_text: str = "Hey! How are you?") -> bool:
    """
    Helper function to send a message in an already-open chat.
    
    Args:
        page: BasePage instance
        message_text: Message to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        logger.info(f"Sending message: '{message_text}'...")
        
        # Find message input field
        message_input_locators = [
            ("xpath", "//*[@class='android.widget.EditText']"),
            ("xpath", "//*[contains(@hint, 'Message') or contains(@hint, 'message')]"),
            ("xpath", "//*[contains(@content-desc, 'Message') or contains(@content-desc, 'message')]"),
            ("id", "dk.doubble.dating:id/message_input"),
            ("id", "dk.doubble.dating:id/edit_message"),
            ("id", "dk.doubble.dating:id/et_message"),
        ]
        
        message_sent = False
        
        for locator_type, locator_value in message_input_locators:
            try:
                if page.is_element_present_silent(locator_type, locator_value, timeout=2):
                    logger.info(f"Found message input: {locator_type}={locator_value[:50]}...")
                    page.enter_text(locator_type, locator_value, message_text, clear_first=True)
                    time.sleep(0.5)
                    
                    # Find and click send button
                    send_locators = [
                        ("xpath", "//*[contains(@content-desc, 'Send') or contains(@content-desc, 'send')]"),
                        ("xpath", "//*[contains(@text, 'Send')]"),
                        ("id", "dk.doubble.dating:id/send"),
                        ("id", "dk.doubble.dating:id/btn_send"),
                    ]
                    
                    for send_loc_type, send_loc_value in send_locators:
                        try:
                            if page.is_element_present_silent(send_loc_type, send_loc_value, timeout=1):
                                logger.info(f"Found send button: {send_loc_type}={send_loc_value[:50]}...")
                                page.tap(send_loc_type, send_loc_value)
                                message_sent = True
                                logger.info(f"✓ Message sent: '{message_text}'")
                                time.sleep(1)
                                break
                        except:
                            continue
                    
                    if message_sent:
                        break
            except Exception as e:
                continue
        
        if not message_sent:
            logger.warning("Could not find message input or send button. Trying alternative: pressing Enter...")
            # Try pressing Enter key
            try:
                page.driver.press_keycode(66)  # KEYCODE_ENTER
                logger.info("Pressed Enter to send message")
                time.sleep(1)
                message_sent = True
            except Exception as e:
                logger.error(f"Could not send message: {e}")
                return False
        
        return message_sent
        
    except Exception as e:
        logger.error(f"Error sending message in chat: {e}", exc_info=True)
        return False


def send_message_to_new_match(page: BasePage) -> bool:
    """
    Send a message to a new match (from the Matched tab).
    
    Args:
        page: BasePage instance
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        logger.info("=" * 60)
        logger.info("PHASE 2A: Sending message to NEW MATCH")
        logger.info("=" * 60)
        
        logger.info("Step 1: Navigating to likes/matches section...")
        time.sleep(1)
        
        # Try to find and click on "Likes" or "Matches" in navigation
        likes_match_locators = [
            ("xpath", "//*[contains(@content-desc, 'Likes') or contains(@content-desc, 'likes')]"),
            ("xpath", "//*[contains(@text, 'Likes') or contains(@text, 'likes')]"),
            ("xpath", "//*[contains(@content-desc, 'Matches') or contains(@content-desc, 'matches')]"),
            ("xpath", "//*[contains(@text, 'Matches') or contains(@text, 'matches')]"),
            ("id", "dk.doubble.dating:id/likes"),
            ("id", "dk.doubble.dating:id/matches"),
            ("accessibility_id", "Likes"),
            ("accessibility_id", "Matches"),
        ]
        
        clicked_likes = False
        for locator_type, locator_value in likes_match_locators:
            try:
                if page.is_element_present_silent(locator_type, locator_value, timeout=1):
                    logger.info(f"Found likes/matches button: {locator_type}={locator_value[:50]}...")
                    page.tap(locator_type, locator_value)
                    clicked_likes = True
                    time.sleep(2)
                    break
            except Exception as e:
                continue
        
        if not clicked_likes:
            logger.warning("Could not find likes/matches button. Trying to navigate manually...")
            page.press_back()
            time.sleep(1)
        
        logger.info("Step 2: Clicking on 'Matched' tab...")
        time.sleep(1)
        
        # Find and click "Matched" tab/button
        matched_locators = [
            ("xpath", "//*[contains(@text, 'Matched') or contains(@text, 'matched')]"),
            ("xpath", "//*[contains(@content-desc, 'Matched') or contains(@content-desc, 'matched')]"),
            ("xpath", "//*[contains(@text, 'Matches')]"),
            ("id", "dk.doubble.dating:id/matched"),
            ("id", "dk.doubble.dating:id/tab_matched"),
        ]
        
        clicked_matched = False
        for locator_type, locator_value in matched_locators:
            try:
                if page.is_element_present_silent(locator_type, locator_value, timeout=1):
                    logger.info(f"Found 'Matched' button: {locator_type}={locator_value[:50]}...")
                    page.tap(locator_type, locator_value)
                    clicked_matched = True
                    time.sleep(2)
                    break
            except Exception as e:
                continue
        
        if not clicked_matched:
            logger.warning("Could not find 'Matched' button. Assuming already on matches screen...")
        
        logger.info("Step 3: Clicking on the first/recent match...")
        time.sleep(1)
        
        # Find and click on the first match
        match_locators = [
            ("xpath", "//*[@clickable='true' and (contains(@class, 'Card') or contains(@class, 'card') or contains(@class, 'Match'))]"),
            ("xpath", "//*[@clickable='true' and contains(@content-desc, 'match')]"),
            ("xpath", "//androidx.recyclerview.widget.RecyclerView//*[@clickable='true']"),
            ("xpath", "//*[contains(@class, 'RecyclerView')]//*[@clickable='true']"),
        ]
        
        clicked_match = False
        for locator_type, locator_value in match_locators:
            try:
                elements = page.find_elements(locator_type, locator_value, timeout=2)
                if elements:
                    logger.info(f"Found {len(elements)} match(es). Clicking the first one...")
                    elements[0].click()
                    clicked_match = True
                    time.sleep(2)
                    break
            except Exception as e:
                continue
        
        if not clicked_match:
            logger.warning("Could not find a match to click. Trying alternative approach...")
            size = page.driver.get_window_size()
            center_x = size["width"] // 2
            center_y = size["height"] // 2
            page.driver.tap([(center_x, center_y)], 100)
            time.sleep(2)
        
        logger.info("Step 4: Scrolling down on match profile...")
        time.sleep(1)
    
        page.swipe_up()
        time.sleep(1)
        page.swipe_up()
        time.sleep(1)
        
        logger.info("Step 5: Finding and clicking 'Private Chat' or message button...")
        time.sleep(1)
        
        # Find and click private chat/message button
        chat_locators = [
            ("xpath", "//*[contains(@text, 'Message') or contains(@text, 'message')]"),
            ("xpath", "//*[contains(@text, 'Chat') or contains(@text, 'chat')]"),
            ("xpath", "//*[contains(@text, 'Send Message')]"),
            ("xpath", "//*[contains(@content-desc, 'Message') or contains(@content-desc, 'message')]"),
            ("xpath", "//*[contains(@content-desc, 'Chat') or contains(@content-desc, 'chat')]"),
            ("id", "dk.doubble.dating:id/message"),
            ("id", "dk.doubble.dating:id/chat"),
            ("id", "dk.doubble.dating:id/btn_message"),
        ]
        
        clicked_chat = False
        for locator_type, locator_value in chat_locators:
            try:
                if page.is_element_present_silent(locator_type, locator_value, timeout=2):
                    logger.info(f"Found chat/message button: {locator_type}={locator_value[:50]}...")
                    page.tap(locator_type, locator_value)
                    clicked_chat = True
                    time.sleep(2)
                    break
            except Exception as e:
                continue
        
        if not clicked_chat:
            logger.warning("Could not find chat button. Trying to scroll more...")
            page.swipe_up()
            time.sleep(1)
            for locator_type, locator_value in chat_locators:
                try:
                    if page.is_element_present_silent(locator_type, locator_value, timeout=1):
                        page.tap(locator_type, locator_value)
                        clicked_chat = True
                        time.sleep(2)
                        break
                except:
                    continue
        
        if not clicked_chat:
            logger.error("Could not find chat button. Cannot send message to new match.")
            return False
        
        # Send the message
        return send_message_in_chat(page, "Hey! How are you?")
        
    except Exception as e:
        logger.error(f"Error sending message to new match: {e}", exc_info=True)
        return False


def send_message_to_existing_conversation(page: BasePage) -> bool:
    """
    Send a message to an existing conversation (from Messages/Chats tab).
    
    Args:
        page: BasePage instance
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        logger.info("")
        logger.info("=" * 60)
        logger.info("PHASE 2B: Sending message to EXISTING CONVERSATION")
        logger.info("=" * 60)
        
        # Press back to get out of the chat from previous step
        logger.info("Going back to navigate to existing conversations...")
        page.press_back()
        time.sleep(1)
        page.press_back()  # May need to go back twice
        time.sleep(1)
        
        logger.info("Step 1: Navigating to likes/matches section...")
        time.sleep(1)
        
        # Navigate to likes/matches section
        likes_match_locators = [
            ("xpath", "//*[contains(@content-desc, 'Likes') or contains(@content-desc, 'likes')]"),
            ("xpath", "//*[contains(@text, 'Likes') or contains(@text, 'likes')]"),
            ("xpath", "//*[contains(@content-desc, 'Matches') or contains(@content-desc, 'matches')]"),
            ("xpath", "//*[contains(@text, 'Matches') or contains(@text, 'matches')]"),
            ("id", "dk.doubble.dating:id/likes"),
            ("id", "dk.doubble.dating:id/matches"),
            ("accessibility_id", "Likes"),
            ("accessibility_id", "Matches"),
        ]
        
        for locator_type, locator_value in likes_match_locators:
            try:
                if page.is_element_present_silent(locator_type, locator_value, timeout=1):
                    logger.info(f"Found likes/matches button: {locator_type}={locator_value[:50]}...")
                    page.tap(locator_type, locator_value)
                    time.sleep(2)
                    break
            except Exception:
                continue
        
        logger.info("Step 2: Looking for 'Messages' or 'Chats' tab...")
        time.sleep(1)
        
        # Find and click "Messages" or "Chats" tab
        messages_locators = [
            ("xpath", "//*[contains(@text, 'Messages') or contains(@text, 'messages')]"),
            ("xpath", "//*[contains(@text, 'Chat') or contains(@text, 'chat')]"),
            ("xpath", "//*[contains(@content-desc, 'Messages') or contains(@content-desc, 'messages')]"),
            ("xpath", "//*[contains(@content-desc, 'Chat') or contains(@content-desc, 'chat')]"),
            ("id", "dk.doubble.dating:id/messages"),
            ("id", "dk.doubble.dating:id/chats"),
            ("id", "dk.doubble.dating:id/tab_messages"),
        ]
        
        clicked_messages = False
        for locator_type, locator_value in messages_locators:
            try:
                if page.is_element_present_silent(locator_type, locator_value, timeout=2):
                    logger.info(f"Found messages/chats button: {locator_type}={locator_value[:50]}...")
                    page.tap(locator_type, locator_value)
                    clicked_messages = True
                    time.sleep(2)
                    break
            except Exception as e:
                continue
        
        if not clicked_messages:
            logger.warning("Could not find Messages/Chats tab. Trying alternative navigation...")
            page.press_back()
            time.sleep(1)
        
        logger.info("Step 3: Clicking on the first existing conversation...")
        time.sleep(1)
        
        # Find and click on the first conversation
        conversation_locators = [
            ("xpath", "//androidx.recyclerview.widget.RecyclerView//*[@clickable='true']"),
            ("xpath", "//*[contains(@class, 'RecyclerView')]//*[@clickable='true']"),
            ("xpath", "//*[@clickable='true' and (contains(@class, 'Conversation') or contains(@class, 'Chat'))]"),
        ]
        
        clicked_conversation = False
        for locator_type, locator_value in conversation_locators:
            try:
                elements = page.find_elements(locator_type, locator_value, timeout=2)
                if elements:
                    logger.info(f"Found {len(elements)} conversation(s). Clicking the first one...")
                    elements[0].click()
                    clicked_conversation = True
                    time.sleep(2)
                    break
            except Exception as e:
                continue
        
        if not clicked_conversation:
            logger.error("Could not find an existing conversation to open.")
            return False
        
        # Send the message
        return send_message_in_chat(page, "Hey! How are you?")
        
    except Exception as e:
        logger.error(f"Error sending message to existing conversation: {e}", exc_info=True)
        return False


def navigate_to_matches_and_send_message(page: BasePage, swipe_page: DoubbleSwipePage):
    """
    Navigate to matches section and send messages:
    1. Send message to 1 new match
    2. Send message to 1 existing conversation
    
    Args:
        page: BasePage instance
        swipe_page: DoubbleSwipePage instance
    """
    try:
        # Send message to 1 new match
        new_match_success = send_message_to_new_match(page)
        
        # Wait a bit between actions
        time.sleep(2)
        
        # Send message to 1 existing conversation
        existing_conv_success = send_message_to_existing_conversation(page)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Match messaging automation completed!")
        logger.info(f"  - New match: {'✓ Message sent' if new_match_success else '✗ Failed'}")
        logger.info(f"  - Existing conversation: {'✓ Message sent' if existing_conv_success else '✗ Failed'}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during match messaging: {e}", exc_info=True)


def main():
    """Main automation function."""
    try:
        logger.info("=" * 60)
        logger.info("Doubble Auto Swipe - Fully Automated")
        logger.info("=" * 60)
        
        # ============================================================
        # CONFIGURATION AND ACTION PLAN (Display first, before driver init)
        # ============================================================
        logger.info("")
        logger.info("=" * 60)
        logger.info("CONFIGURATION")
        logger.info("=" * 60)
        logger.info("Number of swipes: 5")
        logger.info("New matches to message: 1")
        logger.info("Existing conversations to message: 1")
        logger.info("Message to send: 'Hey! How are you?'")
        logger.info("Swipe speed: Ultra-fast (200ms duration)")
        logger.info("Pop-up checks: Every 20 iterations")
        logger.info("Connection recovery: Enabled")
        logger.info("")
        logger.info("=" * 60)
        logger.info("ACTION PLAN - Doubble Automation")
        logger.info("=" * 60)
        logger.info("")
        logger.info("PHASE 1: SWIPING (5 swipes)")
        logger.info("  Step 1.1: Detect current screen")
        logger.info("  Step 1.2: Navigate to swipe screen (if needed)")
        logger.info("  Step 1.3: Perform 5 right swipes (like gestures)")
        logger.info("           - Each swipe: ~0.3 seconds")
        logger.info("           - Total time: ~1.5 seconds")
        logger.info("")
        logger.info("PHASE 2A: NEW MATCH MESSAGING (1 match)")
        logger.info("  Step 2.1: Navigate to Likes/Matches section")
        logger.info("  Step 2.2: Click on 'Matched' tab (recent matches)")
        logger.info("  Step 2.3: Click on the first/recent match")
        logger.info("  Step 2.4: Scroll down on match profile (2 swipes)")
        logger.info("  Step 2.5: Find and click 'Private Chat' / 'Message' button")
        logger.info("  Step 2.6: Find message input field")
        logger.info("  Step 2.7: Type message: 'Hey! How are you?'")
        logger.info("  Step 2.8: Click 'Send' button or press Enter")
        logger.info("")
        logger.info("PHASE 2B: EXISTING CONVERSATION MESSAGING (1 conversation)")
        logger.info("  Step 3.1: Navigate back to Likes/Matches section")
        logger.info("  Step 3.2: Click on 'Messages' or 'Chats' tab")
        logger.info("  Step 3.3: Click on the first existing conversation")
        logger.info("  Step 3.4: Find message input field")
        logger.info("  Step 3.5: Type message: 'Hey! How are you?'")
        logger.info("  Step 3.6: Click 'Send' button or press Enter")
        logger.info("")
        logger.info("=" * 60)
        logger.info("Initializing Appium driver...")
        logger.info("=" * 60)
        logger.info("")
        
        # Automatically start Appium server if not running
        if not check_appium_server_reachable():
            logger.info("Appium server is not running. Attempting to start it automatically...")
            appium_started = start_appium_server()
            if not appium_started:
                logger.error("")
                logger.error("=" * 60)
                logger.error("ERROR: Failed to Start Appium Server")
                logger.error("=" * 60)
                logger.error("")
                logger.error("Could not automatically start the Appium server.")
                logger.error("")
                logger.error("Please try one of the following:")
                logger.error("  1. Install Appium: npm install -g appium")
                logger.error("  2. Start Appium manually in a separate terminal: appium")
                logger.error("  3. Use 'run_auto_swipe.bat' which starts Appium automatically")
                logger.error("")
                logger.error("=" * 60)
                return 1
            else:
                # Appium was just started - wait a bit longer and verify it's ready
                logger.info("Appium server was started. Verifying it's ready...")
                # Wait up to 15 seconds for server to become ready
                for verify_retry in range(5):
                    time.sleep(2)
                    if check_appium_server_reachable():
                        logger.info("[OK] Appium server is confirmed ready")
                        break
                    if verify_retry < 4:
                        logger.info(f"Server not ready yet, waiting 2 seconds... (attempt {verify_retry + 1}/5)")
                else:
                    logger.error("")
                    logger.error("=" * 60)
                    logger.error("ERROR: Appium server is not reachable even after starting!")
                    logger.error("=" * 60)
                    logger.error("")
                    logger.error("The Appium server may have failed to start properly.")
                    logger.error("Please check:")
                    logger.error("  1. Is Appium installed? Run: npm install -g appium")
                    logger.error("  2. Is port 4723 already in use?")
                    logger.error("  3. Try starting Appium manually: appium")
                    logger.error("")
                    logger.error("=" * 60)
                    return 1
        else:
            logger.info("[OK] Appium server is already running")
            # Still verify it's reachable
            if not check_appium_server_reachable():
                logger.warning("Appium server was reported as running but is not reachable")
                logger.warning("Attempting to restart...")
                # Try to start it
                if start_appium_server():
                    logger.info("[OK] Appium server restarted successfully")
                else:
                    logger.error("Failed to restart Appium server")
                    return 1
        logger.info("")
        
        # Check if Android device is connected
        logger.info("Checking for connected Android device...")
        device_connected = False
        device_id = None
        try:
            # Try direct ADB first (faster and more reliable)
            adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
            if not adb_path.exists():
                adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
            
            if adb_path.exists():
                logger.debug(f"Using ADB directly: {adb_path}")
                try:
                    result = subprocess.run(
                        [str(adb_path), "devices"],
                        capture_output=True,
                        text=True,
                        timeout=3  # Short timeout
                    )
                    devices_output = result.stdout
                    logger.debug(f"ADB devices output: {devices_output}")
                    
                    # Check if any device is connected (status should be "device")
                    lines = devices_output.strip().split('\n')
                    for line in lines[1:]:  # Skip header line
                        if line.strip() and '\tdevice' in line:
                            device_connected = True
                            device_id = line.split('\t')[0]
                            logger.info(f"[OK] Android device is connected: {device_id}")
                            break
                except Exception as e:
                    logger.warning(f"Direct ADB check failed: {e}, trying PowerShell...")
                    # Fallback to PowerShell with short timeout
                    try:
                        ps_command = '& "$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe" devices'
                        success, stdout, stderr = run_powershell_command(ps_command, timeout=3)
                        if success and stdout:
                            devices_output = stdout
                            lines = devices_output.strip().split('\n')
                            for line in lines[1:]:
                                if line.strip() and '\tdevice' in line:
                                    device_connected = True
                                    device_id = line.split('\t')[0]
                                    logger.info(f"[OK] Android device is connected: {device_id}")
                                    break
                    except Exception as ps_error:
                        logger.warning(f"PowerShell check also failed: {ps_error}")
            else:
                logger.debug("ADB not found in standard locations, trying PowerShell...")
                # Try PowerShell as last resort
                try:
                    ps_command = '& "$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe" devices'
                    success, stdout, stderr = run_powershell_command(ps_command, timeout=3)
                    if success and stdout:
                        devices_output = stdout
                        lines = devices_output.strip().split('\n')
                        for line in lines[1:]:
                            if line.strip() and '\tdevice' in line:
                                device_connected = True
                                device_id = line.split('\t')[0]
                                logger.info(f"[OK] Android device is connected: {device_id}")
                                break
                except Exception as ps_error:
                    logger.warning(f"PowerShell check failed: {ps_error}")
                
            # Check one more time with detailed diagnostics
            if not device_connected:
                logger.warning("No device detected. Running diagnostic check...")
                try:
                    adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
                    if not adb_path.exists():
                        adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
                    if adb_path.exists():
                        result = subprocess.run(
                            [str(adb_path), "devices", "-l"],  # -l shows more details
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        logger.info(f"Current ADB devices status:\n{result.stdout}")
                        if result.stderr:
                            logger.warning(f"ADB stderr: {result.stderr}")
                except Exception as diag_error:
                    logger.debug(f"Diagnostic check failed: {diag_error}")
            
            if not device_connected:
                logger.error("")
                logger.error("=" * 60)
                logger.error("ERROR: No Android Device Connected")
                logger.error("=" * 60)
                logger.error("")
                logger.error("Please ensure an Android device or emulator is connected and ready.")
                logger.error("")
                logger.error("Attempting to help you start an emulator...")
                
                # Try to list available emulators using PowerShell
                logger.info("Checking for available emulators...")
                list_avds_cmd = '& "$env:LOCALAPPDATA\\Android\\Sdk\\emulator\\emulator.exe" -list-avds'
                success, avd_output, _ = run_powershell_command(list_avds_cmd, timeout=5)
                
                if success and avd_output.strip():
                    avds = [line.strip() for line in avd_output.strip().split('\n') if line.strip()]
                    if avds:
                        logger.info(f"Found {len(avds)} available emulator(s):")
                        for i, avd in enumerate(avds, 1):
                            logger.info(f"  {i}. {avd}")
                        logger.info("")
                        logger.info("Attempting to automatically start the first emulator...")
                        
                        # Try to start the first emulator automatically
                        emulator_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "emulator" / "emulator.exe"
                        if emulator_path.exists():
                            try:
                                logger.info(f"Starting emulator: {avds[0]}")
                                # Start emulator in background
                                emulator_process = subprocess.Popen(
                                    [str(emulator_path), "-avd", avds[0]],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    stdin=subprocess.DEVNULL,
                                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                                )
                                
                                logger.info("Waiting for emulator to boot (this may take 60-120 seconds)...")
                                
                                # Wait for emulator to appear in adb devices (max 180 seconds = 3 minutes)
                                max_wait = 180  # Increased from 90 to 180 seconds
                                waited = 0
                                check_interval = 5  # Check every 5 seconds instead of 3
                                
                                while waited < max_wait:
                                    time.sleep(check_interval)
                                    waited += check_interval
                                    
                                    if waited % 15 == 0:  # Log every 15 seconds
                                        logger.info(f"  Still waiting for emulator to boot... ({waited}/{max_wait} seconds)")
                                    
                                    # Check if emulator is connected
                                    adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
                                    if not adb_path.exists():
                                        adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
                                    
                                    if adb_path.exists():
                                        try:
                                            result = subprocess.run(
                                                [str(adb_path), "devices"],
                                                capture_output=True,
                                                text=True,
                                                timeout=3
                                            )
                                            devices_output = result.stdout
                                            logger.debug(f"ADB devices output: {devices_output}")
                                            lines = devices_output.strip().split('\n')
                                            for line in lines[1:]:
                                                if line.strip() and '\t' in line:
                                                    parts = line.strip().split('\t')
                                                    if len(parts) >= 2:
                                                        device_id = parts[0]
                                                        status = parts[1]
                                                        
                                                        # Check if it's an emulator (by ID pattern or name)
                                                        is_emulator = 'emulator' in device_id.lower() or 'emulator' in line.lower() or device_id.startswith('emulator-')
                                                        
                                                        logger.debug(f"Found device: {device_id}, status: {status}, is_emulator: {is_emulator}")
                                                        
                                                        if status == 'device':
                                                            # Accept any device with 'device' status (emulator or physical device)
                                                            # If we're waiting for an emulator, prefer emulators, but accept any device
                                                            if is_emulator or not device_connected:
                                                                logger.info(f"[OK] Device is ready! Device ID: {device_id}")
                                                                device_connected = True
                                                            
                                                            # Open Doubble app on the emulator
                                                            logger.info("Opening Doubble app on emulator...")
                                                            try:
                                                                # Try using ADB to launch the app
                                                                app_result = subprocess.run(
                                                                    [str(adb_path), "shell", "am", "start", "-a", "android.intent.action.MAIN", 
                                                                     "-c", "android.intent.category.LAUNCHER", "dk.doubble.dating"],
                                                                    capture_output=True,
                                                                    text=True,
                                                                    timeout=5
                                                                )
                                                                if app_result.returncode == 0 and "Error" not in app_result.stderr:
                                                                    logger.info("[OK] Doubble app opened successfully!")
                                                                    time.sleep(3)  # Give app time to launch
                                                                else:
                                                                    # Fallback: try monkey command
                                                                    monkey_result = subprocess.run(
                                                                        [str(adb_path), "shell", "monkey", "-p", "dk.doubble.dating", "-c", 
                                                                         "android.intent.category.LAUNCHER", "1"],
                                                                        capture_output=True,
                                                                        text=True,
                                                                        timeout=10
                                                                    )
                                                                    if monkey_result.returncode == 0:
                                                                        logger.info("[OK] Doubble app opened via monkey command!")
                                                                        time.sleep(3)
                                                                    else:
                                                                        logger.warning("Could not open Doubble app automatically, but emulator is ready")
                                                            except Exception as app_error:
                                                                logger.warning(f"Could not open Doubble app: {app_error}")
                                                                logger.info("Emulator is ready - app will be opened later in the script")
                                                            
                                                            break
                                                        elif status == 'offline':
                                                            # Emulator is starting but not ready yet
                                                            logger.debug(f"Emulator {device_id} is offline (still booting)...")
                                                            break
        
                                            if device_connected:
                                                break
                                        except Exception:
                                            pass
                                    
                                    if waited % 15 == 0:  # Log every 15 seconds
                                        logger.info(f"  Still waiting for emulator to boot... ({waited}/{max_wait} seconds)")
                                
                                if not device_connected:
                                    logger.warning("Emulator did not become ready within timeout period")
                                    logger.warning("You can start it manually with:")
                                    logger.warning(f'  powershell -Command "& \'$env:LOCALAPPDATA\\Android\\Sdk\\emulator\\emulator.exe\' -avd {avds[0]}"')
                                    logger.warning("Then wait for it to fully boot and run the script again")
                            except Exception as e:
                                logger.warning(f"Failed to start emulator automatically: {e}")
                                logger.info("You can start one manually with:")
                                logger.info(f'  powershell -Command "& \'$env:LOCALAPPDATA\\Android\\Sdk\\emulator\\emulator.exe\' -avd {avds[0]}"')
                        else:
                            logger.info("Emulator executable not found. You can start one manually with:")
                            logger.info(f'  powershell -Command "& \'$env:LOCALAPPDATA\\Android\\Sdk\\emulator\\emulator.exe\' -avd {avds[0]}"')
                
                # Only show error and return if device is still not connected
                if not device_connected:
                    logger.error("")
                    logger.error("To check devices manually, run:")
                    logger.error('  powershell -Command "& \'$env:LOCALAPPDATA\\Android\\Sdk\\platform-tools\\adb.exe\' devices"')
                    logger.error("")
                    logger.error("The device should show status 'device' (not 'offline' or 'unauthorized').")
                    logger.error("=" * 60)
                    return 1
                
        except Exception as e:
            # Check if it's a timeout exception without using subprocess in except clause
            if type(e).__name__ == 'TimeoutExpired':
                logger.warning("Device check timed out - cannot verify device connection")
                logger.warning("Continuing anyway...")
            else:
                logger.warning(f"Could not check device connection: {type(e).__name__}: {e}")
                logger.warning("Continuing anyway, but driver initialization may fail if no device is connected")
        
        logger.info("")
        logger.info("Verifying device is fully ready before driver initialization...")
        
        # Wait a bit and verify device is truly ready (not just detected by ADB)
        # Sometimes ADB shows device as "device" but it's still booting
        device_ready = False
        max_ready_checks = 15  # Increased to 15 checks (wait up to 45 seconds)
        for ready_check in range(max_ready_checks):
            try:
                adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
                if not adb_path.exists():
                    adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
                
                if adb_path.exists():
                    # Check multiple properties to ensure device is fully ready
                    try:
                        # Check boot completed
                        boot_result = subprocess.run(
                            [str(adb_path), "shell", "getprop", "sys.boot_completed"],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        # Check if device is ready for input
                        input_result = subprocess.run(
                            [str(adb_path), "shell", "getprop", "dev.bootcomplete"],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        # Check if init.svc.bootanim is stopped (boot animation finished)
                        anim_result = subprocess.run(
                            [str(adb_path), "shell", "getprop", "init.svc.bootanim"],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        
                        boot_done = boot_result.returncode == 0 and boot_result.stdout.strip() == "1"
                        input_ready = input_result.returncode == 0 and input_result.stdout.strip() == "1"
                        anim_stopped = anim_result.returncode == 0 and anim_result.stdout.strip() == "stopped"
                        
                        if boot_done and input_ready and anim_stopped:
                            logger.info("[OK] Device is fully booted and ready (all checks passed)")
                            device_ready = True
                            break
                        else:
                            status = []
                            if not boot_done:
                                status.append("boot not completed")
                            if not input_ready:
                                status.append("input not ready")
                            if not anim_stopped:
                                status.append(f"boot animation: {anim_result.stdout.strip()}")
                            logger.info(f"Device still booting... (check {ready_check + 1}/{max_ready_checks}) - {', '.join(status) if status else 'checking...'}")
                            time.sleep(3)  # Wait 3 seconds between checks
                    except Exception as e:
                        logger.debug(f"Device check error: {e}")
                        time.sleep(3)
            except Exception as e:
                logger.debug(f"ADB path check error: {e}")
                time.sleep(3)
        
        if not device_ready:
            logger.warning("Could not verify device boot status after all checks, but continuing anyway...")
            logger.warning("Driver initialization may take longer or fail if device is not ready")
        
        logger.info("")
        logger.info("Creating Appium driver connection...")
        logger.info("(This may take 30-60 seconds to establish connection and install UiAutomator2)...")
        
        try:
            # Add a timeout wrapper or at least log that we're attempting
            import threading
            
            driver_initialized = False
            driver_result = None
            driver_exception = None
            
            def init_driver():
                nonlocal driver_initialized, driver_result, driver_exception
                try:
                    logger.info("Attempting to connect to Appium server...")
                    logger.info("(Installing UiAutomator2 server on device - this may take 30-60 seconds on first run)...")
                    # Import here to avoid circular imports
                    from drivers import get_driver
                    driver_result = get_driver()
                    driver_initialized = True
                    logger.info("[SUCCESS] Driver created successfully!")
                except Exception as e:
                    driver_exception = e
                    driver_initialized = True
                    logger.error(f"[ERROR] Driver initialization failed: {type(e).__name__}: {e}")
                    import traceback
                    logger.debug(f"Full traceback: {traceback.format_exc()}")
            
            # Start driver initialization in a thread
            init_thread = threading.Thread(target=init_driver, daemon=True)
            init_thread.start()
            
            # Wait with timeout (120 seconds - increased for UiAutomator2 installation on first run)
            # Check progress every 10 seconds
            max_timeout = 120  # Increased from 60 to 120 seconds for first-time UiAutomator2 installation
            waited = 0
            check_interval = 10
            while waited < max_timeout and not driver_initialized:
                init_thread.join(timeout=check_interval)
                waited += check_interval
                if not driver_initialized and init_thread.is_alive():
                    logger.info(f"Still initializing driver... ({waited}/{max_timeout} seconds)")
                    # Check if Appium server is still reachable
                    if not check_appium_server_reachable():
                        logger.warning("Appium server became unreachable during driver initialization!")
                        break
                    # Check if device is still connected
                    try:
                        adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
                        if not adb_path.exists():
                            adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
                        if adb_path.exists():
                            result = subprocess.run(
                                [str(adb_path), "devices"],
                                capture_output=True,
                                text=True,
                                timeout=2
                            )
                            if "device" not in result.stdout:
                                logger.warning("Device disconnected during driver initialization!")
                        break
                    except Exception:
                        pass  # Ignore ADB check errors
            
            if not driver_initialized:
                logger.error("")
                logger.error("=" * 60)
                logger.error("ERROR: Driver Initialization Timed Out")
                logger.error("=" * 60)
                logger.error("")
                logger.error(f"Driver initialization timed out after {max_timeout} seconds.")
                logger.error("")
                logger.error("Attempting automatic recovery...")
                
                # Try to diagnose the issue
                try:
                    adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
                    if not adb_path.exists():
                        adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
                    if adb_path.exists():
                        # Check device status
                        result = subprocess.run(
                            [str(adb_path), "devices"],
                capture_output=True,
                text=True,
                            timeout=3
                        )
                        logger.info(f"Current device status: {result.stdout}")
                        
                        # Check if device is fully booted
                        boot_result = subprocess.run(
                            [str(adb_path), "shell", "getprop", "sys.boot_completed"],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        logger.info(f"Device boot status: {boot_result.stdout.strip()}")
                except Exception as e:
                    logger.debug(f"Diagnostic check failed: {e}")
                
                # Try one more time with a fresh attempt
                logger.info("")
                logger.info("Retrying driver initialization (this may take another 60 seconds)...")
                time.sleep(2)  # Brief pause before retry
                
                try:
                    from drivers import get_driver
                    driver = get_driver()
                    logger.info("[SUCCESS] Driver created on retry!")
                    driver_initialized = True
                    driver_result = driver
                except Exception as retry_error:
                    logger.error("")
                    logger.error("Retry also failed. This usually means:")
                    logger.error("  1. Device is not fully ready (still booting)")
                    logger.error("  2. UiAutomator2 installation is failing")
                    logger.error("  3. Appium cannot communicate with the device")
                    logger.error("")
                    logger.error("Troubleshooting steps:")
                    logger.error("  1. Wait 30-60 seconds for emulator to fully boot")
                    logger.error("  2. Check if device is connected: adb devices")
                    logger.error("  3. Try restarting Appium: appium")
                    logger.error("  4. Try restarting the emulator")
                    logger.error("")
                    logger.error(f"Error: {type(retry_error).__name__}: {retry_error}")
                    logger.error("=" * 60)
                    return 1
            
            if driver_exception:
                logger.error("")
                logger.error("=" * 60)
                logger.error("ERROR: Driver Initialization Failed")
                logger.error("=" * 60)
                logger.error("")
                logger.error(f"Error: {type(driver_exception).__name__}: {driver_exception}")
                logger.error("")
                logger.error("Common causes:")
                logger.error("  1. UiAutomator2 installation failed on device")
                logger.error("  2. Appium server connection issue")
                logger.error("  3. Device compatibility issue")
                logger.error("")
                logger.error("Try:")
                logger.error("  1. Restart the emulator")
                logger.error("  2. Restart Appium server")
                logger.error("  3. Check Appium server logs for errors")
                logger.error("=" * 60)
                return 1
            
            driver = driver_result
            logger.info("[OK] Driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            logger.error("This might mean Appium needs more time to be ready.")
            logger.error("Waiting a bit longer and retrying...")
            time.sleep(3)
            # Retry once
            try:
                logger.info("Retrying driver initialization...")
                driver = get_driver()
                logger.info("[OK] Driver initialized successfully (on retry)")
            except Exception as e2:
                logger.error(f"Driver initialization failed again: {e2}")
                logger.error("Please check your device connection and Appium configuration.")
                raise
        
        # Create page objects
        page = BasePage()
        screen_detector = DoubbleScreenDetector()
        swipe_page = DoubbleSwipePage()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Starting automation...")
        logger.info("=" * 60)
        logger.info("")
        
        # OPTIMIZED: Removed initial wait - start immediately
        # No wait needed - driver is ready
        
        # Check if app is already open
        logger.info("Checking if Doubble app is already open...")
        app_already_open = False
        try:
            current_package = page.get_current_package()
            current_activity = page.get_current_activity()
            logger.info(f"Current app: {current_package}/{current_activity}")
            
            # Check if Doubble app is currently open
            if current_package == "dk.doubble.dating":
                logger.info("[OK] Doubble app is already open!")
                app_already_open = True
        except Exception as e:
            logger.warning(f"Could not get current app info: {e}")
        
        # Launch the Doubble app if not already open
        app_launched = app_already_open
        
        if not app_launched:
            logger.info("App not open. Launching Doubble app...")
        
        # Find ADB path
        adb_path = Path(os.environ.get('LOCALAPPDATA', '')) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
        if not adb_path.exists():
            adb_path = Path("C:/LDPlayer/LDPlayer9/adb.exe")
        
        if not adb_path.exists():
            logger.warning("ADB not found in standard locations. Trying Appium activate_app()...")
            try:
                driver.activate_app("dk.doubble.dating")
                logger.info("[OK] App activated using activate_app()")
                app_launched = True
                time.sleep(3)
            except Exception as e:
                logger.warning(f"activate_app failed: {e}")
        else:
            # Try using Appium activate_app first (simplest)
            try:
                logger.info("Trying activate_app()...")
                driver.activate_app("dk.doubble.dating")
                logger.info("[OK] App activated using activate_app()")
                app_launched = True
                time.sleep(3)
            except Exception as e:
                logger.info(f"activate_app failed, trying ADB methods...")
        
                # Try launcher intent (Android finds activity automatically)
                logger.info("Trying launcher intent...")
            result = subprocess.run(
                [str(adb_path), "shell", "am", "start", "-a", "android.intent.action.MAIN", 
                 "-c", "android.intent.category.LAUNCHER", "dk.doubble.dating"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and "Error" not in result.stderr:
                logger.info("[OK] App launched via launcher intent")
                app_launched = True
                time.sleep(3)
        
                # Try monkey command if launcher intent failed
        if not app_launched:
            logger.info("Trying ADB monkey command...")
            result = subprocess.run(
                [str(adb_path), "shell", "monkey", "-p", "dk.doubble.dating", "-c", 
                 "android.intent.category.LAUNCHER", "1"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("[OK] App launched via ADB monkey command")
                app_launched = True
                time.sleep(3)
        
                    # Try common activity names as last resort
        if not app_launched:
            logger.info("Trying common activity names...")
            common_activities = [
                ".MainActivity",
                ".ui.MainActivity",
                ".SplashActivity", 
                ".LaunchActivity",
            ]
            
            for activity in common_activities:
                result = subprocess.run(
                    [str(adb_path), "shell", "am", "start", "-n", f"dk.doubble.dating/{activity}"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and "Error" not in result.stderr and "does not exist" not in result.stderr:
                    logger.info(f"[OK] App launched with activity: {activity}")
                    app_launched = True
                    time.sleep(3)
                    break
        
        # If still not launched, just continue - app might already be open or user can open it manually
        if not app_launched:
                logger.warning("Could not launch app automatically. Continuing anyway...")
                logger.warning("If app is not open, please open it manually on the emulator.")
                logger.warning("The script will continue and try to detect if app opens.")
                time.sleep(2)
        
        if app_already_open:
            logger.info("[OK] App is already open - ready to proceed!")
        elif app_launched:
            logger.info("[OK] App launched successfully!")
        else:
            logger.info("[OK] Continuing - assuming app will be available...")
        
        # Wait for app to load (if we just launched it)
        # OPTIMIZED: Minimal wait times
        if app_launched and not app_already_open:
            logger.info("Waiting for app to load...")
            time.sleep(2)  # Reduced from 3s to 2s
        # No wait if app is already open - start immediately
        
        # FIRST: Check what screen we're currently on (before any pop-up checks)
        # OPTIMIZED: Ultra-fast detection - minimal checks
        logger.info("=" * 60)
        logger.info("Detecting current screen...")
        logger.info("=" * 60)
        
        current_screen = "unknown"
        try:
            # CRITICAL FIX: Check for swipe screen elements FIRST (most reliable)
            # Activity name can be ambiguous - .MainActivity might be used for multiple screens
            
            # Strategy 1: Check for like button (most reliable swipe screen indicator)
            try:
                if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.1):
                    current_screen = "swipe"
                    logger.info("[FAST] Detected SWIPE screen from like button!")
                    # Get activity for logging
                    try:
                        current_activity = page.get_current_activity()
                        logger.info(f"Current Activity: {current_activity}")
                    except:
                        pass
            except:
                pass
            
            # Strategy 2: Check for swipe-specific UI elements (card stack, discover, etc.)
            if current_screen == "unknown":
                try:
                    # Check for multiple swipe screen indicators with higher confidence
                    swipe_indicators = [
                        ("xpath", "//*[contains(@content-desc, 'Swipe') or contains(@content-desc, 'swipe')]"),
                        ("xpath", "//*[contains(@content-desc, 'Discover') or contains(@content-desc, 'discover')]"),
                        ("xpath", "//*[contains(@content-desc, 'Explore') or contains(@content-desc, 'explore')]"),
                        ("xpath", "//*[@class='androidx.cardview.widget.CardView']"),  # Card stack
                        ("xpath", "//*[contains(@class, 'Card') or contains(@class, 'card')]"),
                    ]
                    
                    found_indicators = 0
                    for loc_type, loc_value in swipe_indicators[:3]:  # Check top 3
                        try:
                            if swipe_page.is_element_present_silent(loc_type, loc_value, timeout=0.05):
                                found_indicators += 1
                        except:
                            continue
                    
                    # If we found at least 1 swipe indicator, likely on swipe screen
                    if found_indicators > 0:
                        current_screen = "swipe"
                        logger.info(f"[FAST] Detected SWIPE screen from {found_indicators} swipe indicator(s)!")
                        try:
                            current_activity = page.get_current_activity()
                            logger.info(f"Current Activity: {current_activity}")
                        except:
                            pass
                except:
                    pass
            
            # Strategy 3: Activity-based detection (less reliable - only as fallback)
            if current_screen == "unknown":
                try:
                    current_activity = page.get_current_activity()
                    logger.info(f"Current Activity: {current_activity}")
                    
                    activity_lower = str(current_activity).lower()
                    if "swipe" in activity_lower or "discover" in activity_lower:
                        current_screen = "swipe"
                        logger.info("[FAST] Detected SWIPE from activity name")
                    elif "match" in activity_lower or "like" in activity_lower:
                        # This might be matches/likes screen, not swipe screen
                        logger.warning("[INFO] Activity suggests MATCHES/LIKES screen - checking elements...")
                        # Still check for like button - might be on swipe after all
                        try:
                            if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.1):
                                current_screen = "swipe"
                                logger.info("[FAST] Actually on SWIPE screen (found like button despite activity name)")
                        except:
                            pass
                    elif "main" in activity_lower or "home" in activity_lower:
                        # Activity says main/home, but could still be swipe screen - CHECK ELEMENTS
                        logger.info("[INFO] Activity suggests HOME/MAIN - verifying with elements...")
                        # Double-check with elements - don't trust activity name alone
                        try:
                            if swipe_page.is_element_present_silent("xpath", "//*[contains(@content-desc, 'Like') or contains(@content-desc, 'like')]", timeout=0.1):
                                current_screen = "swipe"
                                logger.info("[FAST] Actually on SWIPE screen (found like button - activity name was misleading)")
                            else:
                                current_screen = "home"
                                logger.info("[INFO] Confirmed HOME screen (no swipe elements found)")
                        except:
                            current_screen = "home"
                            logger.info("[INFO] Assuming HOME screen (element check failed)")
                except:
                    pass
            
            # Brief logging
            if current_screen == "home":
                logger.info("[INFO] On HOME screen - will navigate to swipe screen")
            elif current_screen == "swipe":
                logger.info("[INFO] Detection shows SWIPE screen - skipping navigation")
            elif current_screen == "login":
                logger.warning("[WARNING] On LOGIN screen - need to log in first")
            else:
                logger.info(f"[INFO] Screen unknown - will attempt navigation")
            
        except Exception as e:
            logger.warning(f"Error during screen detection: {e}")
            logger.info("Will attempt to continue and navigate to swipe screen...")
        
        logger.info("=" * 60)
        
        # OPTIMIZED: Skip navigation if already on swipe screen (activity-based detection is reliable)
        if current_screen == "swipe":
            # Already on swipe screen - skip pop-up check initially for speed, start swiping immediately
            logger.info("[INFO] Already on swipe screen - starting swiping immediately!")
            # Skip initial pop-up check - will be handled in the loop if needed
        
        # If not on swipe screen (or verification failed), navigate
        if current_screen != "swipe":
            # Not on swipe screen - need to navigate
            # Handle any initial pop-ups (silent mode - no error logging)
            dismissed = swipe_page.handle_popups_quiet()
            if dismissed > 0:
                logger.info(f"[!] Dismissed {dismissed} initial pop-up(s)")
            # OPTIMIZED: Removed wait - not needed
            
            # Navigate to swipe screen
            logger.info("Navigating to swipe screen...")
            navigation_success = ensure_on_swipe_screen(page, screen_detector, swipe_page)
            
            if not navigation_success:
                logger.warning("Navigation may not have succeeded, but continuing anyway...")
                logger.warning("If the script doesn't work, please manually navigate to swipe screen.")
                time.sleep(0.5)  # Reduced from 1s to 0.5s
        
        # Do 5 swipes first, then navigate to matches and send messages
        logger.info("Starting: 5 swipes, then navigate to matches...")
        swipe_and_like_loop(swipe_page, page, max_iterations=5)  # Do exactly 5 swipes
        
        # After 5 swipes, navigate to matches and send messages
        logger.info("=" * 60)
        logger.info("5 swipes completed! Navigating to matches...")
        logger.info("=" * 60)
        navigate_to_matches_and_send_message(page, swipe_page)
        
        logger.info("Automation completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 0
    except Exception as e:
        error_message = str(e)
        
        # Check if it's an Appium server not running error - show cleaner message
        if "Appium server is not running" in error_message:
            logger.error("")
            logger.error("=" * 60)
            logger.error("ERROR: Appium Server Not Running")
            logger.error("=" * 60)
            logger.error("")
            logger.error("The Appium server is not running. Please start it before running this script.")
            logger.error("")
            logger.error("Options:")
            logger.error("  1. Use 'run_auto_swipe.bat' - This will start Appium automatically")
            logger.error("  2. Start Appium manually in a separate terminal: appium")
            logger.error("")
            logger.error("Once Appium is running, run this script again.")
            logger.error("=" * 60)
        else:
            # For other errors, show the full traceback
            logger.error(f"Error during automation: {error_message}", exc_info=True)
        
        return 1
    finally:
        logger.info("Cleaning up...")
        close_driver()
        # Only stop Appium if we started it (don't stop if it was already running)
        # We track this with the _appium_process global variable
        stop_appium_server()
        logger.info("Done!")


if __name__ == "__main__":
    sys.exit(main())

