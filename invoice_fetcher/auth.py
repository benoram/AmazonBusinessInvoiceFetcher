"""Authentication module for Amazon Business login."""

import time
import keyring
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from .config import Config
from .exceptions import AuthenticationError, WebDriverError


class AmazonBusinessAuth:
    """Handles authentication with Amazon Business."""

    KEYRING_SERVICE = "amazon-business-invoice-fetcher"

    def __init__(self, config: Config):
        """Initialize the authenticator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.session_cookies: Optional[list] = None

    def _setup_driver(self, interactive: bool = False) -> webdriver.Chrome:
        """Set up and return a Chrome WebDriver instance.

        Args:
            interactive: If True, show browser window for manual SSO login
        """
        try:
            chrome_options = Options()

            # Only run headless if not in interactive mode
            if not interactive and self.config.get("selenium.headless", True):
                chrome_options.add_argument("--headless")

            # Add common Chrome options for better compatibility
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            )

            # Set up Chrome service with auto-downloaded driver
            # Get latest ChromeDriver version
            service = Service(ChromeDriverManager().install())

            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set timeouts
            timeout = self.config.get("selenium.timeout", 30)
            driver.implicitly_wait(timeout)
            driver.set_page_load_timeout(
                self.config.get("selenium.page_load_timeout", 30)
            )

            return driver

        except Exception as e:
            raise WebDriverError(f"Failed to set up Chrome driver: {e}")

    def get_credentials(self) -> tuple[str, str]:
        """Get Amazon Business credentials.

        Returns:
            Tuple of (email, password)

        Raises:
            AuthenticationError: If credentials cannot be obtained
        """
        email = self.config.amazon_email
        if not email:
            raise AuthenticationError("Amazon Business email not configured")

        # Try to get password from config first, then keyring
        password = self.config.amazon_password
        if not password:
            password = keyring.get_password(self.KEYRING_SERVICE, email)

        if not password:
            raise AuthenticationError(
                f"Password not found for {email}. "
                "Set AMAZON_BUSINESS_PASSWORD environment variable or store in keyring."
            )

        return email, password

    def store_password(self, email: str, password: str) -> None:
        """Store password in system keyring.

        Args:
            email: Amazon Business email
            password: Amazon Business password
        """
        keyring.set_password(self.KEYRING_SERVICE, email, password)

    def login(self, interactive: bool = False) -> webdriver.Chrome:
        """Authenticate with Amazon Business and return logged-in driver.

        Args:
            interactive: If True, use interactive mode for SSO login

        Returns:
            Authenticated WebDriver instance

        Raises:
            AuthenticationError: If login fails
            WebDriverError: If there's a WebDriver issue
        """
        if self.driver:
            self.driver.quit()

        # Check if we need interactive mode for SSO
        use_sso = self.config.get("amazon.use_sso", False)
        if use_sso or interactive:
            return self._login_sso()

        self.driver = self._setup_driver(interactive=False)

        try:
            email, password = self.get_credentials()

            # Navigate to Amazon Business
            business_url = self.config.get(
                "amazon.business_url", "https://business.amazon.com"
            )
            self.driver.get(business_url)

            # Wait for and click sign-in button
            wait = WebDriverWait(
                self.driver, self.config.get("amazon.login_timeout", 60)
            )

            # Look for sign-in link/button
            sign_in_selectors = [
                "a[data-nav-role='signin']",
                "a[href*='signin']",
                "#nav-link-accountList",
                ".nav-signin-text",
                "[data-testid='sign-in-button']",
            ]

            sign_in_element = None
            for selector in sign_in_selectors:
                try:
                    sign_in_element = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not sign_in_element:
                raise AuthenticationError(
                    "Could not find sign-in button on Amazon Business page"
                )

            sign_in_element.click()

            # Enter email
            email_field = wait.until(
                EC.presence_of_element_located((By.ID, "ap_email"))
            )
            email_field.clear()
            email_field.send_keys(email)

            # Click continue
            continue_button = self.driver.find_element(By.ID, "continue")
            continue_button.click()

            # Enter password
            password_field = wait.until(
                EC.presence_of_element_located((By.ID, "ap_password"))
            )
            password_field.clear()
            password_field.send_keys(password)

            # Click sign in
            sign_in_button = self.driver.find_element(By.ID, "signInSubmit")
            sign_in_button.click()

            # Wait for successful login (check for common post-login elements)
            try:
                # Wait for one of these elements to appear, indicating successful login
                post_login_selectors = [
                    "#nav-link-accountList",
                    "[data-nav-role='signin']",
                    ".nav-user-name",
                    "#business-nav",
                ]

                for selector in post_login_selectors:
                    try:
                        wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                else:
                    # Check if we're still on a login-related page
                    if (
                        "signin" in self.driver.current_url.lower()
                        or "ap/signin" in self.driver.current_url
                    ):
                        raise AuthenticationError(
                            "Login appears to have failed - still on sign-in page"
                        )

            except TimeoutException:
                # Check for error messages
                error_selectors = [
                    "#auth-error-message-box",
                    ".auth-error-message",
                    "#auth-warning-message-box",
                ]

                for selector in error_selectors:
                    try:
                        error_element = self.driver.find_element(
                            By.CSS_SELECTOR, selector
                        )
                        if error_element.is_displayed():
                            error_text = error_element.text
                            raise AuthenticationError(f"Login failed: {error_text}")
                    except Exception:
                        continue

                raise AuthenticationError(
                    "Login timeout - could not verify successful authentication"
                )

            # Give a moment for any redirects to complete
            time.sleep(2)

            return self.driver

        except AuthenticationError:
            raise
        except Exception as e:
            if self.driver:
                self.driver.quit()
                self.driver = None
            raise AuthenticationError(f"Login failed: {e}")

    def _login_sso(self) -> webdriver.Chrome:
        """Authenticate using SSO/Okta flow.

        Returns:
            Authenticated WebDriver instance

        Raises:
            AuthenticationError: If login fails
        """
        print("\n🔐 SSO Authentication Required")
        print("A browser window will open for you to complete the login process.")
        print("Please log in using your SSO credentials (Okta).\n")

        self.driver = self._setup_driver(interactive=True)

        try:
            # Navigate to Amazon Business
            business_url = self.config.get(
                "amazon.business_url", "https://business.amazon.com"
            )
            self.driver.get(business_url)

            # Wait for user to complete SSO login
            wait = WebDriverWait(
                self.driver, self.config.get("amazon.sso_timeout", 300)  # 5 minutes
            )

            print("Waiting for you to complete the SSO login...")
            print("(This will timeout after 5 minutes)\n")

            # Wait for successful login by checking for post-login elements
            post_login_selectors = [
                "#nav-link-accountList",
                "[data-nav-role='signin']",
                ".nav-user-name",
                "#business-nav",
                "[data-testid='business-header']",
                ".ab-user-menu",
            ]

            logged_in = False
            for selector in post_login_selectors:
                try:
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    # Also check that we're not on a login page
                    current_url = self.driver.current_url.lower()
                    if "signin" not in current_url and "ap/signin" not in current_url:
                        logged_in = True
                        break
                except TimeoutException:
                    continue

            if not logged_in:
                raise AuthenticationError(
                    "SSO login timeout - could not verify successful authentication"
                )

            print("✅ SSO login successful!\n")

            # Save cookies for potential reuse
            self.session_cookies = self.driver.get_cookies()

            # Give a moment for any final redirects
            time.sleep(2)

            return self.driver

        except Exception as e:
            if self.driver:
                self.driver.quit()
                self.driver = None
            raise AuthenticationError(f"SSO login failed: {e}")

    def logout(self) -> None:
        """Log out and close the driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None

    def __enter__(self):
        """Context manager entry."""
        return self.login()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()
