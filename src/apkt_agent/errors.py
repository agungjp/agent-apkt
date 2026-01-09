"""Custom exceptions for APKT Agent."""


class APKTError(Exception):
    """Base exception for APKT Agent."""
    pass


class ConfigError(APKTError):
    """Configuration error."""
    pass


class AuthError(APKTError):
    """Authentication error."""
    pass


class ApktAuthError(AuthError):
    """APKT-specific authentication error."""
    pass


class BrowserError(APKTError):
    """Browser automation error."""
    pass


class ApktDownloadError(BrowserError):
    """Download error for APKT files."""
    pass


class NoDataFoundError(ApktDownloadError):
    """No data found for the selected filters - should skip without retry."""
    pass


class DatasetError(APKTError):
    """Dataset-related error."""
    pass


class ParseError(APKTError):
    """Data parsing error."""
    pass


class ValidationError(APKTError):
    """Data validation error."""
    pass


class SinkError(APKTError):
    """Data sink error."""
    pass
