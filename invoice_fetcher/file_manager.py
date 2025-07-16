"""File management utilities for organizing invoices."""

import re
from pathlib import Path
from typing import Optional
from datetime import datetime
from .exceptions import FileError


class FileManager:
    """Manages file operations and organization for invoices."""

    def __init__(self, base_dir: Path):
        """Initialize the file manager.

        Args:
            base_dir: Base directory for storing invoices
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(
        self, transaction_date: datetime, amount: str, invoice_number: str
    ) -> str:
        """Generate filename according to the specified format.

        Args:
            transaction_date: Date of the transaction
            amount: Transaction amount (e.g., "249.99")
            invoice_number: Amazon invoice number

        Returns:
            Formatted filename
        """
        # Sanitize the amount string to remove currency symbols and spaces
        amount_clean = re.sub(r"[^\d.]", "", str(amount))

        # Sanitize invoice number to be filesystem safe
        invoice_clean = re.sub(r"[^\w\-.]", "", str(invoice_number))

        # Format: {year}-{month}-{date}--{amount}--{invoice_number}.pdf
        filename = (
            f"{transaction_date.year:04d}-"
            f"{transaction_date.month:02d}-"
            f"{transaction_date.day:02d}--"
            f"{amount_clean}--"
            f"{invoice_clean}.pdf"
        )

        return filename

    def get_file_path(
        self, transaction_date: datetime, amount: str, invoice_number: str
    ) -> Path:
        """Get the full file path for an invoice.

        Args:
            transaction_date: Date of the transaction
            amount: Transaction amount
            invoice_number: Amazon invoice number

        Returns:
            Full path where the file should be stored
        """
        year = transaction_date.year
        month = transaction_date.month

        # Create year/month directory structure
        dir_path = self.base_dir / str(year) / f"{month:02d}"
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = self.generate_filename(transaction_date, amount, invoice_number)
        return dir_path / filename

    def file_exists(
        self, transaction_date: datetime, amount: str, invoice_number: str
    ) -> bool:
        """Check if an invoice file already exists.

        Args:
            transaction_date: Date of the transaction
            amount: Transaction amount
            invoice_number: Amazon invoice number

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.get_file_path(transaction_date, amount, invoice_number)
        return file_path.exists()

    def save_invoice(
        self,
        content: bytes,
        transaction_date: datetime,
        amount: str,
        invoice_number: str,
    ) -> Path:
        """Save invoice content to file.

        Args:
            content: PDF content as bytes
            transaction_date: Date of the transaction
            amount: Transaction amount
            invoice_number: Amazon invoice number

        Returns:
            Path to the saved file

        Raises:
            FileError: If there's an error saving the file
        """
        file_path = self.get_file_path(transaction_date, amount, invoice_number)

        try:
            with open(file_path, "wb") as f:
                f.write(content)
            return file_path
        except Exception as e:
            raise FileError(f"Failed to save invoice {invoice_number}: {e}")

    def list_existing_invoices(self, year: Optional[int] = None) -> list:
        """List all existing invoice files.

        Args:
            year: If specified, only list invoices from this year

        Returns:
            List of tuples (file_path, parsed_info) where parsed_info contains
            date, amount, and invoice_number
        """
        invoices = []

        search_dirs = []
        if year:
            year_dir = self.base_dir / str(year)
            if year_dir.exists():
                search_dirs = [year_dir]
        else:
            search_dirs = [
                d for d in self.base_dir.iterdir() if d.is_dir() and d.name.isdigit()
            ]

        for year_dir in search_dirs:
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue

                for file_path in month_dir.glob("*.pdf"):
                    parsed_info = self.parse_filename(file_path.name)
                    if parsed_info:
                        invoices.append((file_path, parsed_info))

        return sorted(invoices, key=lambda x: x[1]["date"])

    def parse_filename(self, filename: str) -> Optional[dict]:
        """Parse invoice filename to extract information.

        Args:
            filename: Invoice filename

        Returns:
            Dictionary with 'date', 'amount', 'invoice_number' or None if parsing fails
        """
        # Remove .pdf extension
        name = filename.replace(".pdf", "")

        # Pattern: YYYY-MM-DD--amount--invoice_number
        pattern = r"^(\d{4})-(\d{2})-(\d{2})--([^-]+)--(.+)$"
        match = re.match(pattern, name)

        if not match:
            return None

        year, month, day, amount, invoice_number = match.groups()

        try:
            date = datetime(int(year), int(month), int(day))
            return {"date": date, "amount": amount, "invoice_number": invoice_number}
        except ValueError:
            return None

    def cleanup_empty_directories(self) -> None:
        """Remove empty year/month directories."""
        try:
            for year_dir in self.base_dir.iterdir():
                if not year_dir.is_dir() or not year_dir.name.isdigit():
                    continue

                for month_dir in year_dir.iterdir():
                    if month_dir.is_dir() and not any(month_dir.iterdir()):
                        month_dir.rmdir()

                # Remove year directory if empty
                if year_dir.is_dir() and not any(year_dir.iterdir()):
                    year_dir.rmdir()
        except Exception:
            # Ignore cleanup errors
            pass
