"""
Selenium browser utilities for scraping IMDb pages that block regular requests.
Auto-detects platform: uses Chrome on Linux (GitHub Actions), Edge on Windows.
"""
from typing import Optional
import platform
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


def _is_windows() -> bool:
    return platform.system() == "Windows"


class SeleniumBrowser:
    """Manages a headless browser for scraping. Uses Edge on Windows, Chrome on Linux."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def _create_chrome_driver(self):
        """Create Chrome WebDriver for Linux/GitHub Actions."""
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()

        if self.headless:
            options.add_argument("--headless=new")

        # Suppress console logging
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--disable-logging")

        # Common anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Disable images for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2
        }
        options.add_experimental_option("prefs", prefs)

        # Exclude automation flags and logging
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)

        # Remove webdriver property to avoid detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

        return driver

    def _create_edge_driver(self):
        """Create Edge WebDriver for Windows."""
        from selenium.webdriver.edge.options import Options as EdgeOptions

        options = EdgeOptions()

        if self.headless:
            options.add_argument("--headless=new")

        # Suppress console logging
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--disable-logging")

        # Common anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")

        # Disable images for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2
        }
        options.add_experimental_option("prefs", prefs)

        # Exclude automation flags and logging
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Edge(options=options)

        # Remove webdriver property to avoid detection
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

        return driver

    def _create_driver(self):
        """Create WebDriver based on platform."""
        if _is_windows():
            return self._create_edge_driver()
        else:
            return self._create_chrome_driver()

    def start(self):
        """Start the browser if not already running."""
        if self.driver is None:
            self.driver = self._create_driver()

    def stop(self):
        """Stop the browser and clean up."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def fetch_page(self, url: str, wait_for_selector: Optional[str] = None, timeout: int = 10) -> BeautifulSoup:
        """
        Fetch a page and return BeautifulSoup object.

        Args:
            url: URL to fetch
            wait_for_selector: Optional CSS selector to wait for before returning
            timeout: Max seconds to wait for page/element

        Returns:
            BeautifulSoup object of the page
        """
        self.start()

        self.driver.get(url)

        # Always wait a bit for JS to execute
        time.sleep(3)

        if wait_for_selector:
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                )
            except Exception:
                pass  # Continue even if element not found

        page_source = self.driver.page_source
        return BeautifulSoup(page_source, 'html.parser')

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Singleton instance for reuse across requests
_browser_instance: Optional[SeleniumBrowser] = None


def get_browser(headless: bool = True) -> SeleniumBrowser:
    """Get or create a shared browser instance."""
    global _browser_instance
    if _browser_instance is None:
        _browser_instance = SeleniumBrowser(headless=headless)
    return _browser_instance


def fetch_with_selenium(url: str, wait_for_selector: Optional[str] = None, timeout: int = 10) -> BeautifulSoup:
    """
    Convenience function to fetch a page using Selenium.

    Args:
        url: URL to fetch
        wait_for_selector: Optional CSS selector to wait for
        timeout: Max seconds to wait

    Returns:
        BeautifulSoup object of the page
    """
    browser = get_browser()
    return browser.fetch_page(url, wait_for_selector, timeout)


def cleanup_browser():
    """Clean up the shared browser instance."""
    global _browser_instance
    if _browser_instance:
        _browser_instance.stop()
        _browser_instance = None
