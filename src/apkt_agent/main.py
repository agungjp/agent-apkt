"""Main application module."""

from .config import load_config
from .logging_ import setup_logger, get_logger


def run() -> None:
    """Run the application."""
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return
    
    # Setup logger
    logger = setup_logger()
    logger.info("APKT Agent started")
    
    # Application logic will be implemented here
    logger.info("Application initialized successfully")
