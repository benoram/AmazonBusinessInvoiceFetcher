"""Tests for file manager module."""

import tempfile
from datetime import datetime
from pathlib import Path

from invoice_fetcher.file_manager import FileManager


class TestFileManager:
    """Test file management functionality."""

    def test_generate_filename(self):
        """Test filename generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            date = datetime(2024, 3, 15)
            filename = fm.generate_filename(date, "249.99", "123-4567890-1234567")

            expected = "2024-03-15--249.99--123-4567890-1234567.pdf"
            assert filename == expected

    def test_generate_filename_sanitized(self):
        """Test filename generation with sanitization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            date = datetime(2024, 3, 15)
            filename = fm.generate_filename(date, "$249.99", "123-4567890-1234567")

            expected = "2024-03-15--249.99--123-4567890-1234567.pdf"
            assert filename == expected

    def test_get_file_path(self):
        """Test file path generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            date = datetime(2024, 3, 15)
            file_path = fm.get_file_path(date, "249.99", "123-4567890-1234567")

            expected_path = (
                Path(temp_dir)
                / "2024"
                / "03"
                / "2024-03-15--249.99--123-4567890-1234567.pdf"
            )
            assert file_path == expected_path
            assert file_path.parent.exists()  # Directory should be created

    def test_file_exists(self):
        """Test file existence check."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            date = datetime(2024, 3, 15)

            # File doesn't exist initially
            assert not fm.file_exists(date, "249.99", "123-4567890-1234567")

            # Create the file
            file_path = fm.get_file_path(date, "249.99", "123-4567890-1234567")
            file_path.touch()

            # Now it should exist
            assert fm.file_exists(date, "249.99", "123-4567890-1234567")

    def test_save_invoice(self):
        """Test saving invoice content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            date = datetime(2024, 3, 15)
            content = b"fake pdf content"

            file_path = fm.save_invoice(content, date, "249.99", "123-4567890-1234567")

            assert file_path.exists()

            with open(file_path, "rb") as f:
                saved_content = f.read()

            assert saved_content == content

    def test_parse_filename(self):
        """Test filename parsing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            filename = "2024-03-15--249.99--123-4567890-1234567.pdf"
            parsed = fm.parse_filename(filename)

            assert parsed is not None
            assert parsed["date"] == datetime(2024, 3, 15)
            assert parsed["amount"] == "249.99"
            assert parsed["invoice_number"] == "123-4567890-1234567"

    def test_parse_filename_invalid(self):
        """Test parsing invalid filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            filename = "invalid-filename.pdf"
            parsed = fm.parse_filename(filename)

            assert parsed is None

    def test_list_existing_invoices(self):
        """Test listing existing invoices."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(Path(temp_dir))

            # Create some test invoices
            dates_and_invoices = [
                (datetime(2024, 3, 15), "249.99", "123-4567890-1234567"),
                (datetime(2024, 3, 16), "150.00", "123-4567890-1234568"),
                (datetime(2023, 12, 25), "75.50", "123-4567890-1234569"),
            ]

            for date, amount, invoice_num in dates_and_invoices:
                fm.save_invoice(b"fake content", date, amount, invoice_num)

            # List all invoices
            invoices = fm.list_existing_invoices()
            assert len(invoices) == 3

            # List invoices for specific year
            invoices_2024 = fm.list_existing_invoices(2024)
            assert len(invoices_2024) == 2

            invoices_2023 = fm.list_existing_invoices(2023)
            assert len(invoices_2023) == 1
