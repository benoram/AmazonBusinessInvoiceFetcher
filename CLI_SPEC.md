# Amazon Business Invoice Fetcher - CLI Application Specification

## Overview
A command-line application that automatically downloads invoices from Amazon Business accounts and organizes them in a local directory structure by year and month for easy reconciliation with credit card statements.

## Core Functionality

### Primary Command: `fetch`
```bash
invoice-fetcher fetch --team <team_name>
```

**Behavior:**
- Retrieves invoices from the past 90 days for the specified team
- Downloads PDF invoices to organized directory structure
- Skips invoices that already exist locally
- Provides progress feedback and summary of downloaded invoices

### File Organization
**Directory Structure:**
```
invoices/
├── 2024/
│   ├── 01/
│   ├── 02/
│   └── ...
└── 2025/
    ├── 01/
    └── ...
```

**File Naming Convention:**
```
{transaction_year}-{transaction_month}-{transaction_date}--{amount}--{invoice_number}.pdf
```

**Example:**
```
2024-03-15--249.99--123-4567890-1234567.pdf
```

## Technical Architecture

### Recommended Technology Stack
- **Language**: Python 3.9+
- **CLI Framework**: Click or Typer
- **HTTP Client**: requests or httpx
- **Authentication**: Selenium WebDriver (for Amazon Business login)
- **PDF Handling**: Built-in file operations
- **Configuration**: YAML or JSON config file

### Core Components

#### 1. Authentication Module
- Handle Amazon Business login via web automation
- Maintain session cookies for API calls
- Support MFA if required
- Support SSO authentication with interactive browser login

#### 2. Invoice API Client
- Interface with Amazon Business invoice endpoints
- Filter invoices by date range (90 days) and team
- Extract invoice metadata (date, amount, number)

#### 3. File Manager
- Create directory structure
- Generate standardized filenames
- Check for existing files to avoid duplicates
- Download and save PDF files

#### 4. CLI Interface
- Command parsing and validation
- Progress indicators
- Error handling and user feedback
- Configuration management

## Configuration

### Config File: `~/.invoice-fetcher/config.yaml`
```yaml
amazon_business:
  base_url: "https://business.amazon.com"
  login_timeout: 30
  
download:
  base_directory: "./invoices"
  date_range_days: 90
  
teams:
  - engineering
  - marketing
  - finance
```

### Environment Variables
- `AMAZON_BUSINESS_EMAIL`: Login email
- `AMAZON_BUSINESS_PASSWORD`: Login password (optional, can prompt)

## Command Line Interface

### Main Command
```bash
invoice-fetcher fetch --team <team_name> [options]
```

### Options
- `--team <name>`: Required. Specify team name for invoice filtering
- `--output-dir <path>`: Override default output directory
- `--days <number>`: Override default 90-day lookback (default: 90)
- `--dry-run`: Show what would be downloaded without actually downloading
- `--verbose`: Enable detailed logging
- `--config <path>`: Use custom config file location
- `--sso`: Use SSO authentication (opens browser for interactive login)

### Additional Commands
```bash
invoice-fetcher setup                 # Initial setup and credential configuration
invoice-fetcher setup --sso           # Setup with SSO authentication (no password needed)
invoice-fetcher list-invoices         # List all downloaded invoices
invoice-fetcher list-invoices --team engineering --year 2024  # Filtered list
```

## Error Handling

### Authentication Errors
- Invalid credentials
- MFA required
- Session timeout

### Network Errors
- Connection failures
- Rate limiting
- API unavailability

### File System Errors
- Permission issues
- Disk space
- Invalid paths

## Security Considerations

### Credential Management
- Never store passwords in plain text
- Support keychain integration on macOS
- Prompt for password if not in environment

### Data Protection
- Store invoices in user-specified directory
- No cloud upload or external data sharing
- Secure session management

## Success Criteria

### Functional Requirements
- ✅ Downloads invoices for specified team
- ✅ Organizes files by year/month structure
- ✅ Uses consistent naming convention
- ✅ Avoids duplicate downloads
- ✅ Covers 90-day lookback period

### Non-Functional Requirements
- ✅ Runs on Apple Silicon Mac
- ✅ Simple command-line interface
- ✅ Reliable authentication handling
- ✅ Clear progress feedback
- ✅ Robust error handling

## Future Enhancements (Out of Scope)
- Multi-account support
- GUI interface
- Automated scheduling
- Integration with accounting software
- Custom date range selection
- Bulk export features

## Development Timeline
1. **Phase 1**: Core authentication and API client
2. **Phase 2**: File management and organization
3. **Phase 3**: CLI interface and commands
4. **Phase 4**: Error handling and edge cases
5. **Phase 5**: Testing and documentation