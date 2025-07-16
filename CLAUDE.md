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

# Run the application
python -m invoice_fetcher fetch --team engineering

# Development commands
python -m pytest                    # Run tests
python -m black .                   # Format code
python -m flake8 .                  # Lint code
python -m mypy .                    # Type checking
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