"""Tests for configuration module."""

import os
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch

from invoice_fetcher.config import Config
from invoice_fetcher.exceptions import ConfigurationError


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        """Test default configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config = Config(config_file)

            assert config.get("selenium.headless") is True
            assert config.get("selenium.timeout") == 30
            assert config.download_dir == Config.DEFAULT_DOWNLOAD_DIR

    def test_load_config_file(self):
        """Test loading configuration from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"

            test_config = {
                "download_dir": "/custom/path",
                "selenium": {"headless": False, "timeout": 60},
            }

            with open(config_file, "w") as f:
                yaml.dump(test_config, f)

            config = Config(config_file)

            assert config.get("download_dir") == "/custom/path"
            assert config.get("selenium.headless") is False
            assert config.get("selenium.timeout") == 60

    def test_environment_variables(self):
        """Test loading configuration from environment variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"

            with patch.dict(
                os.environ,
                {
                    "AMAZON_BUSINESS_EMAIL": "test@example.com",
                    "SELENIUM_HEADLESS": "false",
                    "SELENIUM_TIMEOUT": "45",
                },
            ):
                config = Config(config_file)

                assert config.amazon_email == "test@example.com"
                assert config.get("selenium.headless") is False
                assert config.get("selenium.timeout") == 45

    def test_validation_missing_email(self):
        """Test validation fails when email is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            # Create a config without email and test validation
            config = Config(config_file)
            # Mock the get method to return None for amazon.email
            with patch.object(
                config,
                "get",
                side_effect=lambda key, default=None: (
                    None if key == "amazon.email" else config._config.get(key, default)
                ),
            ):
                with pytest.raises(ConfigurationError, match="email not configured"):
                    config.validate()

    def test_create_default_config(self):
        """Test creating default configuration file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config = Config(config_file)

            config.create_default_config()

            assert config_file.exists()

            with open(config_file, "r") as f:
                loaded_config = yaml.safe_load(f)

            assert "download_dir" in loaded_config
            assert "selenium" in loaded_config

    def test_email_from_config_file(self):
        """Test loading email from config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"

            test_config = {"amazon": {"email": "config@example.com"}}

            with open(config_file, "w") as f:
                yaml.dump(test_config, f)

            config = Config(config_file)
            assert config.amazon_email == "config@example.com"

    def test_env_var_overrides_config_file(self):
        """Test that environment variable takes precedence over config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"

            test_config = {"amazon": {"email": "config@example.com"}}

            with open(config_file, "w") as f:
                yaml.dump(test_config, f)

            with patch.dict(os.environ, {"AMAZON_BUSINESS_EMAIL": "env@example.com"}):
                config = Config(config_file)
                assert config.amazon_email == "env@example.com"

    def test_email_validation_with_config_file(self):
        """Test validation passes when email is in config file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"

            test_config = {"amazon": {"email": "valid@example.com"}}

            with open(config_file, "w") as f:
                yaml.dump(test_config, f)

            config = Config(config_file)
            config.validate()  # Should not raise

    def test_default_config_includes_email(self):
        """Test that DEFAULT_CONFIG includes email field."""
        # Import fresh to avoid side effects from other tests
        from invoice_fetcher.config import Config as FreshConfig

        assert "email" in FreshConfig.DEFAULT_CONFIG["amazon"]
        assert FreshConfig.DEFAULT_CONFIG["amazon"]["email"] is None
