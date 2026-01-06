# APKT Agent

Automated data extraction agent for APKT (Application for Power Knowledge Tool) - PLN's power quality data reporting system.

## Project Structure

```
.
├── src/apkt_agent/              # Source code (src layout)
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   ├── cli.py                   # CLI menu interface
│   ├── config.py                # Configuration management
│   ├── workspace.py             # Run context and workspace management
│   ├── logging_.py              # Logging setup
│   ├── models.py                # Data models
│   ├── errors.py                # Custom exceptions
│   ├── browser/                 # Browser automation
│   │   ├── __init__.py
│   │   ├── driver.py            # Playwright driver management
│   │   ├── auth.py              # Authentication handling
│   │   ├── nav.py               # Navigation helpers
│   │   └── download.py          # File download handling
│   ├── datasets/                # Dataset definitions and handlers
│   │   ├── __init__.py
│   │   ├── base.py              # Base dataset class
│   │   ├── registry.py          # Dataset registry
│   │   └── se004/               # SE004 dataset implementations
│   │       ├── __init__.py
│   │       ├── kumulatif.py
│   │       ├── rolling.py
│   │       ├── gangguan.py
│   │       ├── parser.py
│   │       └── schema.py
│   ├── transform/               # Data transformation
│   │   ├── __init__.py
│   │   ├── validate.py          # Data validation
│   │   └── normalize.py         # Data normalization
│   ├── output/                  # Output writers
│   │   ├── __init__.py
│   │   └── csv_writer.py        # CSV output
│   └── sinks/                   # Data sinks
│       ├── __init__.py
│       ├── api.py               # API sink
│       └── sheets.py            # Google Sheets sink
├── workspace/                   # Runtime workspace (git-ignored)
│   ├── runs/                    # Individual run directories
│   └── latest/                  # Latest run symlink
├── config.example.yaml          # Example configuration
├── pyproject.toml              # Project metadata
├── README.md                   # This file
└── .gitignore                  # Git ignore rules
```

## Setup

### Prerequisites

- Python 3.10+
- pip or uv

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd ods-apkt
```

2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. For development:

```bash
pip install -e ".[dev]"
```

5. Copy and configure:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

## Usage

### Run CLI Menu

```bash
python -m apkt_agent
```

Or using the installed script:

```bash
apkt-agent
```

### CLI Options

The CLI provides an interactive menu for:

- Dataset selection (SE004 Kumulatif, Rolling, Gangguan)
- Period selection
- Snapshot date configuration
- Run execution
- Result review

### Configuration

Edit `config.yaml` (based on `config.example.yaml`):

```yaml
apkt:
  login_url: "https://new-apkt.pln.co.id/login"
  iam_login_url: "https://iam.pln.co.id/auth/login?grant=..."
  iam_totp_url_prefix: "https://iam.pln.co.id/auth/mfa/.../totp"

datasets:
  se004_kumulatif:
    url: "https://new-apktss.pln.co.id/home/laporan-saidi-saifi-kumulatif-se004"
    unit_text_default: "11 - WILAYAH ACEH"
    period_default: "202512"

workspace:
  root: "./workspace"

runtime:
  headless: false
```

## Development

### Run Tests

```bash
pytest
pytest --cov=src/apkt_agent
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type checking
mypy src/
```

### Pre-commit Hooks

```bash
pre-commit install
```

## Workspace

- `workspace/runs/` - Individual run directories with structure:

  - `YYYYMMDD_HHMMSS_<dataset>_<period>_<rand4>/`
    - `raw/excel/` - Downloaded Excel files
    - `parsed/` - Parsed data files
    - `logs/` - Run logs
    - `manifest.json` - Run metadata

- `workspace/latest/` - Symlink to latest run

## License

MIT
