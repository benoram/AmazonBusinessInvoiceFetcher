"""Command line interface for the Amazon Business Invoice Fetcher."""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from .config import Config
from .auth import AmazonBusinessAuth
from .client import InvoiceClient
from .file_manager import FileManager
from .exceptions import (
    InvoiceFetcherError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    FileError,
)

console = Console()


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]Success:[/green] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]Info:[/blue] {message}")


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Amazon Business Invoice Fetcher

    A CLI tool for automatically downloading and organizing invoices from
    Amazon Business.
    """
    pass


@main.command()
@click.option("--team", required=True, help="Team name for organizing invoices")
@click.option(
    "--days", default=90, help="Number of days to look back for invoices (default: 90)"
)
@click.option(
    "--config", type=click.Path(exists=True), help="Path to configuration file"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without actually downloading",
)
def fetch(team: str, days: int, config: str, dry_run: bool):
    """Fetch invoices from Amazon Business for the specified team."""

    try:
        # Load configuration
        config_path = Path(config) if config else None
        cfg = Config(config_path)
        cfg.validate()

        print_info(f"Starting invoice fetch for team: {team}")
        print_info(f"Looking back {days} days")
        print_info(f"Download directory: {cfg.download_dir}")

        if dry_run:
            print_info("DRY RUN MODE - No files will be downloaded")

        # Set up file manager
        team_dir = cfg.download_dir / team
        file_manager = FileManager(team_dir)

        # Authenticate and get invoices
        with console.status("[bold green]Authenticating with Amazon Business..."):
            auth = AmazonBusinessAuth(cfg)
            driver = auth.login()

        print_success("Successfully authenticated with Amazon Business")

        try:
            client = InvoiceClient(cfg, driver)

            with console.status("[bold green]Fetching recent orders..."):
                orders = client.get_recent_orders(days)

            print_info(f"Found {len(orders)} orders in the past {days} days")

            if not orders:
                print_info("No orders found")
                return

            # Process orders
            downloaded_count = 0
            skipped_count = 0
            error_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Processing invoices...", total=len(orders))

                for order in orders:
                    order_num = order.get("order_number", "Unknown")
                    order_date = order.get("date")
                    order_total = order.get("total", "0.00")
                    invoice_url = order.get("invoice_url")

                    progress.update(task, description=f"Processing order {order_num}")

                    if not invoice_url:
                        print_error(f"No invoice URL found for order {order_num}")
                        error_count += 1
                        progress.advance(task)
                        continue

                    if not order_date:
                        print_error(f"No date found for order {order_num}")
                        error_count += 1
                        progress.advance(task)
                        continue

                    # Check if file already exists
                    if file_manager.file_exists(order_date, order_total, order_num):
                        print_info(f"Invoice {order_num} already exists, skipping")
                        skipped_count += 1
                        progress.advance(task)
                        continue

                    if dry_run:
                        filename = file_manager.generate_filename(
                            order_date, order_total, order_num
                        )
                        print_info(f"Would download: {filename}")
                        downloaded_count += 1
                        progress.advance(task)
                        continue

                    # Download invoice
                    try:
                        invoice_content = client.download_invoice(invoice_url)
                        file_path = file_manager.save_invoice(
                            invoice_content, order_date, order_total, order_num
                        )
                        print_success(f"Downloaded: {file_path.name}")
                        downloaded_count += 1
                    except (NetworkError, FileError) as e:
                        print_error(f"Failed to download invoice {order_num}: {e}")
                        error_count += 1

                    progress.advance(task)

        finally:
            auth.logout()

        # Print summary
        summary_table = Table(title="Download Summary")
        summary_table.add_column("Status", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")

        summary_table.add_row("Downloaded", str(downloaded_count))
        summary_table.add_row("Skipped (already exists)", str(skipped_count))
        summary_table.add_row("Errors", str(error_count))
        summary_table.add_row("Total processed", str(len(orders)))

        console.print(summary_table)

        if error_count > 0:
            sys.exit(1)

    except ConfigurationError as e:
        print_error(f"Configuration error: {e}")
        sys.exit(1)
    except AuthenticationError as e:
        print_error(f"Authentication error: {e}")
        sys.exit(1)
    except InvoiceFetcherError as e:
        print_error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print_info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


@main.command()
@click.option("--config", type=click.Path(), help="Path to configuration file")
def setup(config: str):
    """Set up configuration and credentials."""

    try:
        config_path = Path(config) if config else Config.DEFAULT_CONFIG_FILE
        cfg = Config(config_path)

        console.print(
            Panel.fit("Amazon Business Invoice Fetcher Setup", style="bold blue")
        )

        # Create default config if it doesn't exist
        if not config_path.exists():
            cfg.create_default_config()
            print_success(f"Created default configuration at {config_path}")

        # Prompt for email if not configured
        email = cfg.amazon_email
        if not email:
            email = click.prompt("Amazon Business email")

        # Prompt for password and store in keyring
        import getpass

        password = getpass.getpass("Amazon Business password: ")

        auth = AmazonBusinessAuth(cfg)
        auth.store_password(email, password)

        print_success("Credentials stored securely in system keyring")
        print_info(f"Configuration file: {config_path}")
        print_info(f"Download directory: {cfg.download_dir}")

        # Test authentication
        console.print("\n[bold yellow]Testing authentication...[/bold yellow]")

        try:
            with auth:
                print_success("Authentication test successful!")
        except AuthenticationError as e:
            print_error(f"Authentication test failed: {e}")
            sys.exit(1)

    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)


@main.command()
@click.option("--team", help="Team name to list invoices for (optional)")
@click.option("--year", type=int, help="Year to filter invoices (optional)")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to configuration file"
)
def list_invoices(team: str, year: int, config: str):
    """List existing invoices."""

    try:
        config_path = Path(config) if config else None
        cfg = Config(config_path)

        if team:
            base_dir = cfg.download_dir / team
        else:
            base_dir = cfg.download_dir

        if not base_dir.exists():
            print_info("No invoices found")
            return

        if team:
            file_manager = FileManager(base_dir)
            invoices = file_manager.list_existing_invoices(year)
        else:
            # List all teams
            teams = [d for d in base_dir.iterdir() if d.is_dir()]
            invoices = []
            for team_dir in teams:
                fm = FileManager(team_dir)
                team_invoices = fm.list_existing_invoices(year)
                for file_path, info in team_invoices:
                    info["team"] = team_dir.name
                    invoices.append((file_path, info))

        if not invoices:
            print_info("No invoices found")
            return

        # Create table
        table = Table(title="Existing Invoices")
        if not team:
            table.add_column("Team", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Amount", justify="right", style="yellow")
        table.add_column("Invoice #", style="blue")
        table.add_column("File", style="dim")

        for file_path, info in invoices:
            row = []
            if not team:
                row.append(info.get("team", "Unknown"))
            row.extend(
                [
                    info["date"].strftime("%Y-%m-%d"),
                    f"${info['amount']}",
                    info["invoice_number"],
                    file_path.name,
                ]
            )
            table.add_row(*row)

        console.print(table)
        print_info(f"Total: {len(invoices)} invoices")

    except Exception as e:
        print_error(f"Failed to list invoices: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
