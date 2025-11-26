"""Page Object Model module for Android automation framework."""

from .base_page import BasePage
from .login_page import LoginPage
from .home_page import HomePage
from .doubble_screens import DoubbleScreenDetector
from .doubble_swipe_page import DoubbleSwipePage

__all__ = ["BasePage", "LoginPage", "HomePage", "DoubbleScreenDetector", "DoubbleSwipePage"]

