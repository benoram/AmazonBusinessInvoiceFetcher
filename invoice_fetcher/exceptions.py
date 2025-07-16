"""Custom exceptions for the Amazon Business Invoice Fetcher."""


class InvoiceFetcherError(Exception):
    """Base exception for all invoice fetcher errors."""

    pass


class AuthenticationError(InvoiceFetcherError):
    """Raised when authentication with Amazon Business fails."""

    pass


class ConfigurationError(InvoiceFetcherError):
    """Raised when there's an issue with configuration."""

    pass


class NetworkError(InvoiceFetcherError):
    """Raised when there's a network-related error."""

    pass


class FileError(InvoiceFetcherError):
    """Raised when there's an issue with file operations."""

    pass


class InvoiceNotFoundError(InvoiceFetcherError):
    """Raised when an expected invoice cannot be found."""

    pass


class WebDriverError(InvoiceFetcherError):
    """Raised when there's an issue with the web driver."""

    pass
