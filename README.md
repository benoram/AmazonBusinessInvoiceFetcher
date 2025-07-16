# Amazon Business Invoice Fetcher

A command-line tool for automatically downloading and organizing invoices from Amazon Business accounts. This tool helps streamline expense tracking and credit card reconciliation by downloading invoices from the past 90 days and organizing them by team and date.

## Features

- **Automated Invoice Download**: Fetch invoices from Amazon Business for the past 90 days
- **Team Organization**: Organize invoices by team for better expense tracking
- **Smart File Naming**: Invoices are saved with descriptive filenames including date, amount, and invoice number
- **Duplicate Prevention**: Skip files that already exist locally
- **Secure Authentication**: Uses system keyring for secure credential storage
- **Progress Tracking**: Rich console output with progress indicators
- **Dry Run Mode**: Preview what would be downloaded without actually downloading

## Installation

### Prerequisites

- Python 3.9 or higher
- Google Chrome browser (latest version recommended for web automation)
- macOS (tested on Apple Silicon Macs)
- Amazon Business account with invoice access

### Setting Up Amazon Business

Before using this tool, ensure you have:

1. **Amazon Business Account**: You need access to an Amazon Business account with permission to view invoices
2. **Invoice Access**: Make sure your account has the necessary permissions to view and download invoices
3. **Two-Factor Authentication**: If your account has 2FA enabled, you may need to adjust the login timeout settings

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AmazonBusinessInvoiceFetcher
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package**:
   ```bash
   pip install -e .
   ```

## Configuration

### Environment Variables

You can configure the application using environment variables:

```bash
# Required: Your Amazon Business email (can also be set in config.yaml)
export AMAZON_BUSINESS_EMAIL="your-email@company.com"

# Optional: Password (if not set, will be prompted and stored securely)
export AMAZON_BUSINESS_PASSWORD="your-password"

# Optional: Custom download directory
export INVOICE_DOWNLOAD_DIR="~/Documents/invoices"

# Optional: Selenium settings
export SELENIUM_HEADLESS="true"
export SELENIUM_TIMEOUT="30"
```

**Note**: The Amazon Business email can also be configured in the config file under `amazon.email`. Environment variables take precedence over config file values.

### Configuration File

The tool creates a configuration file at `~/.invoice-fetcher/config.yaml` on first run. You can customize:

```yaml
# Download directory
download_dir: "~/Downloads/invoices"

# Selenium WebDriver settings
selenium:
  driver: "chrome"
  headless: true
  timeout: 30
  page_load_timeout: 30

# Amazon Business settings
amazon:
  business_url: "https://business.amazon.com"
  login_timeout: 60

# Logging
logging:
  level: "INFO"
  file: null
```

## Usage

### Initial Setup

Run the setup command to configure credentials:

```bash
invoice-fetcher setup
```

This will:
- Create a default configuration file
- Prompt for your Amazon Business email and password
- Store credentials securely in your system keyring
- Test the authentication

### Fetching Invoices

**Basic usage** - Download invoices for a specific team:
```bash
invoice-fetcher fetch --team engineering
```

**With custom time range**:
```bash
invoice-fetcher fetch --team marketing --days 30
```

**Dry run** - See what would be downloaded without actually downloading:
```bash
invoice-fetcher fetch --team engineering --dry-run
```

### Listing Existing Invoices

**List all invoices**:
```bash
invoice-fetcher list-invoices
```

**List invoices for a specific team**:
```bash
invoice-fetcher list-invoices --team engineering
```

**List invoices for a specific year**:
```bash
invoice-fetcher list-invoices --year 2024
```

**List invoices for a specific team and year**:
```bash
invoice-fetcher list-invoices --team engineering --year 2024
```

## File Organization

Invoices are automatically organized in the following structure:

```
~/Downloads/invoices/
├── engineering/
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── 2024-01-15--249.99--123-4567890-1234567.pdf
│   │   │   └── 2024-01-20--75.50--123-4567890-1234568.pdf
│   │   └── 02/
│   │       └── 2024-02-03--150.00--123-4567890-1234569.pdf
│   └── 2023/
│       └── 12/
│           └── 2023-12-25--99.99--123-4567890-1234570.pdf
└── marketing/
    └── 2024/
        └── 01/
            └── 2024-01-10--199.99--123-4567890-1234571.pdf
```

### File Naming Convention

Invoice files are named using the format:
```
{YYYY}-{MM}-{DD}--{amount}--{invoice_number}.pdf
```

Example: `2024-03-15--249.99--123-4567890-1234567.pdf`

## Development

### Setting Up Development Environment

1. **Clone and set up**:
   ```bash
   git clone <repository-url>
   cd AmazonBusinessInvoiceFetcher
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install in development mode**:
   ```bash
   pip install -e .
   ```

### Running Tests

```bash
# Run all tests
python3 -m pytest

# Run tests with coverage
python3 -m pytest --cov

# Run specific test file
python3 -m pytest tests/test_cli.py

# Run tests with verbose output
python3 -m pytest -v
```

### Code Quality

```bash
# Format code
python3 -m black .

# Check code style
python3 -m flake8 . --max-line-length=88

# Type checking
python3 -m mypy invoice_fetcher/

# Run all quality checks
python3 -m black . && python3 -m flake8 . --max-line-length=88 && python3 -m mypy invoice_fetcher/ && python3 -m pytest
```

### Building Distribution

```bash
# Install build tools
pip install --upgrade build

# Build distribution packages
python3 -m build

# The built packages will be in the dist/ directory
```

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**:
   - The tool automatically downloads the latest Chrome driver version
   - Chrome version 138+ is supported with automatic driver management
   - If you encounter issues, ensure Chrome is updated to the latest version
   - For headless mode issues, try setting `SELENIUM_HEADLESS=false`

2. **Authentication Problems**:
   - Check that your Amazon Business email and password are correct
   - If you have 2FA enabled, you may need to increase the login timeout
   - Try running the setup command again to re-store credentials

3. **Network Issues**:
   - Ensure you have a stable internet connection
   - If behind a corporate firewall, you may need to configure proxy settings
   - Try increasing the timeout values in the configuration

4. **Permission Errors**:
   - Make sure you have write permissions to the download directory
   - Check that your Amazon Business account has invoice access permissions

### Debug Mode

For debugging issues, you can:

1. **Enable verbose logging**:
   ```bash
   # Set in config.yaml
   logging:
     level: "DEBUG"
   ```

2. **Run in non-headless mode**:
   ```bash
   export SELENIUM_HEADLESS=false
   invoice-fetcher fetch --team engineering
   ```

3. **Use dry run mode**:
   ```bash
   invoice-fetcher fetch --team engineering --dry-run
   ```

## Security

- **Credential Storage**: Passwords are stored securely using the system keyring
- **Local Files Only**: All invoices are stored locally; no data is sent to external servers
- **Secure Session Management**: Web sessions are properly managed and cleaned up
- **No Credential Logging**: Passwords and sensitive information are never logged

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and code quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter issues or have questions:

1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information about the problem

## Disclaimer

This tool is for legitimate business use only. Always ensure you comply with Amazon's terms of service and your organization's policies when using automated tools to access business accounts.