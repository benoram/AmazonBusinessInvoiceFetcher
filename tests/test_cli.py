"""Tests for CLI module."""

from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from invoice_fetcher.cli import main


class TestCLI:
    """Test CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Amazon Business Invoice Fetcher" in result.output

    def test_fetch_help(self):
        """Test fetch command help."""
        result = self.runner.invoke(main, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "--team" in result.output
        assert "--days" in result.output

    def test_fetch_missing_team(self):
        """Test fetch command without required team parameter."""
        result = self.runner.invoke(main, ["fetch"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @patch("invoice_fetcher.cli.Config")
    @patch("invoice_fetcher.cli.AmazonBusinessAuth")
    @patch("invoice_fetcher.cli.InvoiceClient")
    @patch("invoice_fetcher.cli.FileManager")
    def test_fetch_dry_run(
        self, mock_file_manager, mock_client, mock_auth, mock_config
    ):
        """Test fetch command in dry run mode."""
        # Mock configuration
        from pathlib import Path

        mock_cfg = MagicMock()
        mock_cfg.download_dir = Path("/tmp/invoices")
        mock_config.return_value = mock_cfg

        # Mock authentication
        mock_driver = MagicMock()
        mock_auth_instance = MagicMock()
        mock_auth_instance.login.return_value = mock_driver
        mock_auth_instance.__enter__.return_value = mock_driver
        mock_auth_instance.__exit__.return_value = None
        mock_auth.return_value = mock_auth_instance

        # Mock client
        mock_client_instance = MagicMock()
        mock_client_instance.get_recent_orders.return_value = []
        mock_client.return_value = mock_client_instance

        # Mock file manager
        mock_fm = MagicMock()
        mock_file_manager.return_value = mock_fm

        result = self.runner.invoke(
            main, ["fetch", "--team", "engineering", "--dry-run"]
        )

        # Should not exit with error for successful dry run
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output

    def test_setup_help(self):
        """Test setup command help."""
        result = self.runner.invoke(main, ["setup", "--help"])
        assert result.exit_code == 0
        assert "--config" in result.output

    def test_list_invoices_help(self):
        """Test list-invoices command help."""
        result = self.runner.invoke(main, ["list-invoices", "--help"])
        assert result.exit_code == 0
        assert "--team" in result.output
        assert "--year" in result.output
