"""Configuration management for APKT Agent."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .errors import ConfigError


class Config:
    """Configuration manager for APKT Agent."""
    
    REQUIRED_KEYS = {
        'apkt': ['login_url', 'iam_login_url', 'iam_totp_url_prefix'],
        'datasets': [],
        'workspace': ['root'],
        'runtime': ['headless'],
    }

    def __init__(self, config_dict: Dict[str, Any], config_path: Optional[Path] = None):
        """Initialize Config with a configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
            config_path: Path to the configuration file (optional)
            
        Raises:
            ConfigError: If required keys are missing
        """
        self.data = config_dict
        self.config_path = config_path or Path('config.yaml')
        self._validate()
        self._validate_google_sheets()

    def _validate(self) -> None:
        """Validate configuration has all required keys.
        
        Raises:
            ConfigError: If required keys are missing
        """
        for top_key, sub_keys in self.REQUIRED_KEYS.items():
            if top_key not in self.data:
                raise ConfigError(f"Missing required config section: {top_key}")
            
            if sub_keys:  # Check sub-keys only if list is not empty
                for sub_key in sub_keys:
                    if sub_key not in self.data[top_key]:
                        raise ConfigError(
                            f"Missing required config key: {top_key}.{sub_key}"
                        )

    def _validate_google_sheets(self) -> None:
        """Validate Google Sheets configuration if enabled.
        
        Raises:
            ConfigError: If google_sheets is enabled but required keys are missing
        """
        gs_config = self.data.get('google_sheets', {})
        
        if not gs_config.get('enabled', False):
            return
        
        required_keys = ['spreadsheet_id', 'worksheet_name', 'credentials_json_path']
        for key in required_keys:
            if not gs_config.get(key):
                raise ConfigError(
                    f"google_sheets.enabled=true but missing required key: google_sheets.{key}"
                )
        
        # Validate credentials file exists
        creds_path = Path(gs_config['credentials_json_path'])
        if not creds_path.exists():
            raise ConfigError(
                f"Google Sheets credentials file not found: {creds_path}\n"
                f"Please ensure the Service Account JSON file exists at the specified path."
            )

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'apkt.login_url')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value

    def __getitem__(self, key: str) -> Any:
        """Get configuration section.
        
        Args:
            key: Section name
            
        Returns:
            Configuration section
        """
        return self.data[key]


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file.

    Attempts to load config.yaml first from multiple locations:
    1. Provided config_path (if specified)
    2. ./credentials/config.yaml
    3. ./config.yaml
    4. ./config.example.yaml
    
    Args:
        config_path: Optional path to config file. If not provided, searches
                    for config.yaml in credentials/ folder first, then root.
                    
    Returns:
        Config object
        
    Raises:
        ConfigError: If configuration file not found or invalid
    """
    if config_path:
        config_file = Path(config_path)
    else:
        # Search for config files in order of preference
        project_root = Path.cwd()
        search_paths = [
            project_root / 'credentials' / 'config.yaml',  # First priority
            project_root / 'config.yaml',                   # Second priority
            project_root / 'config.example.yaml'            # Fallback
        ]
        
        config_file = None
        for path in search_paths:
            if path.exists():
                config_file = path
                break
        
        if not config_file:
            raise ConfigError(
                f"Configuration file not found in any of: "
                f"{', '.join(str(p) for p in search_paths)}"
            )
    
    if not config_file.exists():
        raise ConfigError(f"Configuration file not found: {config_file}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse configuration file: {e}")
    except IOError as e:
        raise ConfigError(f"Failed to read configuration file: {e}")
    
    if not config_dict:
        raise ConfigError(f"Configuration file is empty: {config_file}")
    
    return Config(config_dict, config_path=config_file)
