"""Amazon Business invoice client for fetching invoices."""

import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .config import Config
from .exceptions import NetworkError, InvoiceNotFoundError


class InvoiceClient:
    """Client for fetching invoices from Amazon Business."""

    def __init__(self, config: Config, driver: webdriver.Chrome):
        """Initialize the invoice client.

        Args:
            config: Configuration object
            driver: Authenticated WebDriver instance
        """
        self.config = config
        self.driver = driver
        self.session = requests.Session()

        # Copy cookies from selenium to requests session
        self._sync_cookies()

    def _sync_cookies(self) -> None:
        """Sync cookies from Selenium driver to requests session."""
        for cookie in self.driver.get_cookies():
            self.session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain"),
                path=cookie.get("path"),
            )

    def navigate_to_orders(self) -> None:
        """Navigate to the orders/invoices page."""
        try:
            # Try different possible URLs for orders
            order_urls = [
                "https://business.amazon.com/orders",
                "https://business.amazon.com/orders/history",
                "https://business.amazon.com/your-account/orders",
            ]

            wait = WebDriverWait(self.driver, 30)

            for url in order_urls:
                try:
                    self.driver.get(url)
                    # Wait for the page to load and check if we're on an orders page
                    time.sleep(3)

                    # Look for order-related elements
                    order_indicators = [
                        "[data-testid='order-card']",
                        ".order-card",
                        "#ordersContainer",
                        ".a-section.a-spacing-none.order-info",
                        "[data-test-id='order-tile']",
                    ]

                    for selector in order_indicators:
                        try:
                            wait.until(
                                EC.presence_of_element_located(
                                    (By.CSS_SELECTOR, selector)
                                )
                            )
                            return  # Successfully found orders page
                        except TimeoutException:
                            continue

                except Exception:
                    continue

            # If we get here, try to find orders link in navigation
            nav_selectors = [
                "a[href*='orders']",
                "a[href*='order-history']",
                "#nav-orders",
                "[data-nav-ref='nav_orders']",
            ]

            for selector in nav_selectors:
                try:
                    orders_link = self.driver.find_element(By.CSS_SELECTOR, selector)
                    orders_link.click()
                    time.sleep(3)
                    return
                except NoSuchElementException:
                    continue

            raise InvoiceNotFoundError("Could not navigate to orders page")

        except Exception as e:
            raise InvoiceNotFoundError(f"Failed to navigate to orders: {e}")

    def get_recent_orders(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get recent orders from the past specified days.

        Args:
            days: Number of days to look back

        Returns:
            List of order dictionaries with basic information
        """
        self.navigate_to_orders()

        orders = []
        cutoff_date = datetime.now() - timedelta(days=days)

        try:
            # Wait for orders to load
            # wait = WebDriverWait(self.driver, 30)

            # Scroll and load more orders if needed
            last_height = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

            while True:
                # Scroll down to load more orders
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(2)

                # Check if new content loaded
                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    break
                last_height = new_height

                # Look for "Load more" or similar buttons
                load_more_selectors = [
                    "button[data-testid='load-more']",
                    ".load-more-button",
                    "button[aria-label*='more']",
                ]

                for selector in load_more_selectors:
                    try:
                        load_more = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if load_more.is_displayed() and load_more.is_enabled():
                            load_more.click()
                            time.sleep(3)
                            break
                    except NoSuchElementException:
                        continue

            # Find all order elements
            order_selectors = [
                "[data-testid='order-card']",
                ".order-card",
                ".a-section.a-spacing-none.order-info",
                "[data-test-id='order-tile']",
            ]

            order_elements = []
            for selector in order_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        order_elements = elements
                        break
                except NoSuchElementException:
                    continue

            if not order_elements:
                raise InvoiceNotFoundError("No order elements found on page")

            for order_elem in order_elements:
                try:
                    order_data = self._extract_order_data(order_elem)
                    if (
                        order_data
                        and order_data.get("date", datetime.min) >= cutoff_date
                    ):
                        orders.append(order_data)
                except Exception as e:
                    # Log error but continue with other orders
                    print(f"Error extracting order data: {e}")
                    continue

            return orders

        except Exception as e:
            raise InvoiceNotFoundError(f"Failed to get recent orders: {e}")

    def _extract_order_data(self, order_element) -> Optional[Dict[str, Any]]:
        """Extract order data from an order element.

        Args:
            order_element: Selenium WebElement representing an order

        Returns:
            Dictionary with order information or None if extraction fails
        """
        try:
            order_data = {}

            # Try to find order number
            order_num_selectors = [
                "[data-testid='order-number']",
                ".order-number",
                ".order-info-item:contains('Order')",
                "[class*='order-number']",
            ]

            for selector in order_num_selectors:
                try:
                    elem = order_element.find_element(By.CSS_SELECTOR, selector)
                    text = elem.text.strip()
                    # Extract order number from text like "Order # 123-4567890-1234567"
                    import re

                    match = re.search(r"#?\s*(\d{3}-\d{7}-\d{7})", text)
                    if match:
                        order_data["order_number"] = match.group(1)
                        break
                except Exception:
                    continue

            # Try to find order date
            date_selectors = [
                "[data-testid='order-date']",
                ".order-date",
                "[class*='order-date']",
                ".date-info",
            ]

            for selector in date_selectors:
                try:
                    elem = order_element.find_element(By.CSS_SELECTOR, selector)
                    date_text = elem.text.strip()
                    # Parse common date formats
                    order_data["date"] = self._parse_date(date_text)
                    if order_data["date"]:
                        break
                except Exception:
                    continue

            # Try to find order total
            total_selectors = [
                "[data-testid='order-total']",
                ".order-total",
                "[class*='total']",
                ".price",
            ]

            for selector in total_selectors:
                try:
                    elem = order_element.find_element(By.CSS_SELECTOR, selector)
                    total_text = elem.text.strip()
                    # Extract price from text like "$249.99"
                    import re

                    match = re.search(r"\$?(\d+\.?\d*)", total_text)
                    if match:
                        order_data["total"] = match.group(1)
                        break
                except Exception:
                    continue

            # Try to find invoice/receipt link
            invoice_selectors = [
                "a[href*='invoice']",
                "a[href*='receipt']",
                "a[data-testid*='invoice']",
                ".invoice-link",
            ]

            for selector in invoice_selectors:
                try:
                    elem = order_element.find_element(By.CSS_SELECTOR, selector)
                    order_data["invoice_url"] = elem.get_attribute("href")
                    break
                except Exception:
                    continue

            # Return order data if we found at least order number and date
            if "order_number" in order_data and "date" in order_data:
                return order_data

            return None

        except Exception:
            return None

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date string into datetime object.

        Args:
            date_text: Date string to parse

        Returns:
            Parsed datetime or None if parsing fails
        """
        import re
        from dateutil.parser import parse

        try:
            # Clean up the date text
            date_text = re.sub(r"[^\w\s,/-]", "", date_text)
            date_text = date_text.strip()

            # Try to parse with dateutil
            return parse(date_text)
        except Exception:
            return None

    def download_invoice(self, invoice_url: str) -> bytes:
        """Download invoice PDF from URL.

        Args:
            invoice_url: URL to the invoice PDF

        Returns:
            PDF content as bytes

        Raises:
            NetworkError: If download fails
        """
        try:
            # Sync cookies again in case they've been updated
            self._sync_cookies()

            # Add common headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/pdf,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": self.driver.current_url,
            }

            response = self.session.get(invoice_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Verify it's actually a PDF
            content_type = response.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not invoice_url.endswith(".pdf"):
                # Try to navigate with selenium if direct download fails
                return self._download_with_selenium(invoice_url)

            return response.content

        except requests.RequestException as e:
            raise NetworkError(f"Failed to download invoice from {invoice_url}: {e}")

    def _download_with_selenium(self, invoice_url: str) -> bytes:
        """Download PDF using Selenium navigation.

        Args:
            invoice_url: URL to navigate to

        Returns:
            PDF content as bytes
        """
        try:
            # Navigate to the invoice URL
            self.driver.get(invoice_url)
            time.sleep(3)

            # Look for download link or PDF embed
            pdf_selectors = [
                "a[href$='.pdf']",
                "iframe[src*='pdf']",
                "embed[src*='pdf']",
                "[data-testid='download-pdf']",
            ]

            for selector in pdf_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    pdf_url = elem.get_attribute("src") or elem.get_attribute("href")
                    if pdf_url:
                        return self.download_invoice(pdf_url)
                except Exception:
                    continue

            raise NetworkError("Could not find PDF download link")

        except Exception as e:
            raise NetworkError(f"Selenium PDF download failed: {e}")
