"""
Main entry point for running Android automation tests.

This script initializes logging, runs tests, and handles cleanup.
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pytest
from drivers import DriverFactory, close_driver


def setup_logging():
    """
    Configure logging for the automation framework.
    
    Creates log directory if it doesn't exist and sets up
    both file and console handlers.
    """
    # Load config to get logging settings
    config = DriverFactory.load_config()
    log_config = config["logging"]
    
    # Create logs directory
    log_dir = project_root / log_config["log_dir"]
    log_dir.mkdir(exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{timestamp}_{log_config['log_file']}"
    
    # Configure logging level
    log_level = getattr(logging, log_config["level"].upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (if enabled)
    if log_config.get("console_output", True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    logging.info("=" * 60)
    logging.info("Android Automation Framework - Test Run Started")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 60)
    
    return log_file


def main():
    """Main function to run the automation tests."""
    try:
        # Setup logging
        log_file = setup_logging()
        logger = logging.getLogger(__name__)
        
        logger.info("Initializing test environment...")
        
        # Verify configuration
        config = DriverFactory.load_config()
        logger.info(f"App package: {config['android']['app_package']}")
        logger.info(f"App activity: {config['android']['app_activity']}")
        logger.info(f"Appium server: {config['appium']['server_url']}")
        logger.info(f"Preserve login state: noReset={config['android']['no_reset']}")
        
        # Run pytest
        logger.info("Starting test execution...")
        logger.info("-" * 60)
        
        # Pytest arguments
        pytest_args = [
            "tests/",
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            f"--log-file={log_file}",  # Log file
            "--log-file-level=INFO",  # Log level for file
        ]
        
        # Add additional pytest arguments from command line if provided
        if len(sys.argv) > 1:
            pytest_args.extend(sys.argv[1:])
        
        exit_code = pytest.main(pytest_args)
        
        logger.info("-" * 60)
        if exit_code == 0:
            logger.info("All tests passed!")
        else:
            logger.warning(f"Tests completed with exit code: {exit_code}")
        
        return exit_code
        
    except KeyboardInterrupt:
        logging.warning("Test execution interrupted by user")
        return 130
    except Exception as e:
        logging.error(f"Fatal error during test execution: {str(e)}", exc_info=True)
        return 1
    finally:
        # Cleanup
        logging.info("Cleaning up...")
        close_driver()
        logging.info("Test run completed")
        logging.info("=" * 60)


if __name__ == "__main__":
    sys.exit(main())

