# Amazon Business Invoice Fetcher - Claude Context

## Project Overview
A Python CLI application that automatically downloads invoices from Amazon Business accounts and organizes them locally by year/month for easy credit card reconciliation.

## Core Functionality
- **Main Command**: `invoice-fetcher fetch --team <team_name>`
- **Purpose**: Download invoices from past 90 days for specified team
- **File Organization**: `{year}/{month}/{year}-{month}-{date}--{amount}--{invoice_number}.pdf`
- **Duplicate Prevention**: Skip files that already exist locally

## Technology Stack
- **Language**: Python 3.9+
- **CLI Framework**: Click or Typer
- **Web Automation**: Selenium WebDriver (for Amazon Business login)
- **HTTP Client**: requests or httpx
- **Target Platform**: Apple Silicon Mac

## Key Development Commands
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run the application
invoice-fetcher fetch --team engineering
# or
python -m invoice_fetcher.cli fetch --team engineering

# Build and packaging commands
python setup.py sdist bdist_wheel    # Build distribution packages
pip install --upgrade build          # Install build tool
python -m build                      # Modern build command

# Test commands
python -m pytest                     # Run all tests
python -m pytest -v                  # Run tests with verbose output
python -m pytest --cov               # Run tests with coverage
python -m pytest tests/test_cli.py   # Run specific test file
python -m pytest -k "test_config"    # Run tests matching pattern

# Code quality commands
python -m black .                    # Format code
python -m black --check .            # Check formatting without changes
python -m flake8 .                   # Lint code
python -m flake8 --max-line-length=88 .  # Lint with Black-compatible line length
python -m mypy .                     # Type checking
python -m mypy invoice_fetcher/       # Type check specific package

# Combined quality check
python -m black . && python -m flake8 . && python -m mypy . && python -m pytest

# Application commands
invoice-fetcher setup                 # Initial setup and credential configuration
invoice-fetcher setup --sso           # Setup with SSO authentication (no password needed)
invoice-fetcher fetch --team engineering --days 30  # Fetch invoices for specific team
invoice-fetcher fetch --team marketing --dry-run     # Dry run mode
invoice-fetcher fetch --team engineering --sso       # Fetch with SSO authentication
invoice-fetcher list-invoices         # List all downloaded invoices
invoice-fetcher list-invoices --team engineering --year 2024  # Filtered list

# Development utilities
python -c "import invoice_fetcher; print(invoice_fetcher.__version__)"  # Check version
pip show invoice-fetcher              # Show package information
pip list | grep invoice               # List related packages
```

## Project Structure
```
invoice_fetcher/
├── __init__.py
├── cli.py              # Click/Typer CLI interface
├── auth.py             # Amazon Business authentication
├── client.py           # Invoice API client
├── file_manager.py     # File organization and download
├── config.py           # Configuration handling
└── exceptions.py       # Custom exceptions

tests/
├── test_cli.py
├── test_auth.py
├── test_client.py
└── test_file_manager.py

config/
└── config.yaml         # Default configuration

docs/
└── CLI_SPEC.md         # Detailed specification
```

## Configuration
- **Config File**: `~/.invoice-fetcher/config.yaml`
- **Environment Variables**: 
  - `AMAZON_BUSINESS_EMAIL`: Login email
  - `AMAZON_BUSINESS_PASSWORD`: Login password (optional)

## Security Notes
- Never commit credentials to repository
- Use keychain integration on macOS when possible
- Store invoices only in user-specified local directories
- Implement secure session management for Amazon Business

## Development Guidelines
- Follow Python PEP 8 style guidelines
- Use type hints throughout the codebase
- Implement comprehensive error handling
- Add progress indicators for long-running operations
- Write unit tests for all core functionality

## File Naming Convention
Invoice PDFs are saved with this exact format:
`{transaction_year}-{transaction_month}-{transaction_date}--{amount}--{invoice_number}.pdf`

Example: `2024-03-15--249.99--123-4567890-1234567.pdf`

## Target User
Single user (developer) running on Apple Silicon Mac for personal invoice management and credit card reconciliation.