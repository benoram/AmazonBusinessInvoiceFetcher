"""Configuration management for the invoice fetcher."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .exceptions import ConfigurationError


class Config:
    """Configuration manager for the invoice fetcher."""

    DEFAULT_CONFIG_DIR = Path.home() / ".invoice-fetcher"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
    DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "invoices"

    DEFAULT_CONFIG = {
        "download_dir": str(DEFAULT_DOWNLOAD_DIR),
        "selenium": {
            "driver": "chrome",
            "headless": True,
            "timeout": 30,
            "page_load_timeout": 30,
        },
        "amazon": {
            "business_url": "https://business.amazon.com",
            "login_timeout": 60,
        },
        "logging": {
            "level": "INFO",
            "file": None,
        },
    }

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_file: Path to configuration file. If None, uses default location.
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self._config = self.DEFAULT_CONFIG.copy()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Load from file if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    file_config = yaml.safe_load(f) or {}
                self._merge_config(file_config)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load config file {self.config_file}: {e}"
                )

        # Override with environment variables
        self._load_env_vars()

    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """Merge new configuration into existing config."""

        def merge_dicts(base: Dict[str, Any], new: Dict[str, Any]) -> None:
            for key, value in new.items():
                if (
                    key in base
                    and isinstance(base[key], dict)
                    and isinstance(value, dict)
                ):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value

        merge_dicts(self._config, new_config)

    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "AMAZON_BUSINESS_EMAIL": ["amazon", "email"],
            "AMAZON_BUSINESS_PASSWORD": ["amazon", "password"],
            "INVOICE_DOWNLOAD_DIR": ["download_dir"],
            "SELENIUM_HEADLESS": ["selenium", "headless"],
            "SELENIUM_TIMEOUT": ["selenium", "timeout"],
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                converted_value: Any = value
                if env_var in ["SELENIUM_HEADLESS"]:
                    converted_value = value.lower() in ("true", "1", "yes")
                elif env_var in ["SELENIUM_TIMEOUT"]:
                    try:
                        converted_value = int(value)
                    except ValueError:
                        continue

                # Set the value in config
                current: Dict[str, Any] = self._config
                for key in config_path[:-1]:
                    current = current.setdefault(key, {})
                current[config_path[-1]] = converted_value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split(".")
        current: Any = self._config

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def create_default_config(self) -> None:
        """Create a default configuration file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, "w") as f:
            yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, indent=2)

    @property
    def download_dir(self) -> Path:
        """Get the download directory as a Path object."""
        return Path(self.get("download_dir", self.DEFAULT_DOWNLOAD_DIR))

    @property
    def amazon_email(self) -> Optional[str]:
        """Get Amazon Business email."""
        return self.get("amazon.email")

    @property
    def amazon_password(self) -> Optional[str]:
        """Get Amazon Business password."""
        return self.get("amazon.password")

    def validate(self) -> None:
        """Validate the configuration."""
        if not self.amazon_email:
            raise ConfigurationError(
                "Amazon Business email not configured. "
                "Set AMAZON_BUSINESS_EMAIL environment variable or add to config file."
            )
