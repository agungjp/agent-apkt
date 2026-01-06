"""Logging configuration for APKT Agent."""

import logging
import sys
from pathlib import Path
from typing import Optional

from .workspace import RunContext


class ColoredFormatter(logging.Formatter):
    """Formatter that adds color to console output."""
    
    # ANSI color codes
    GREY = '\x1b[38;21m'
    BLUE = '\x1b[38;5;39m'
    YELLOW = '\x1b[38;5;226m'
    RED = '\x1b[38;5;196m'
    BOLD_RED = '\x1b[31;1m'
    RESET = '\x1b[0m'
    
    COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: BLUE,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color."""
        log_color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str = 'apkt_agent',
    level: int = logging.INFO,
    ctx: Optional[RunContext] = None,
) -> logging.Logger:
    """Setup logger with console and optional file handlers.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        ctx: Optional RunContext for file logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if context is provided
    if ctx:
        log_file = ctx.logs_dir / 'agent.log'
        
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except IOError as e:
            logger.warning(f"Failed to create file handler for {log_file}: {e}")
    
    return logger


def get_logger(name: str = 'apkt_agent') -> logging.Logger:
    """Get or create logger.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
