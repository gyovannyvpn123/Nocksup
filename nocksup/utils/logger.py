"""
Logging utilities for the nocksup library.
"""
import os
import logging
from datetime import datetime

# Default logging format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logger(name, level=None, log_file=None, format_str=None):
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        level: Logging level (default: from environment or INFO)
        log_file: File to write logs to (default: None, stdout only)
        format_str: Logging format string
        
    Returns:
        Logger instance
    """
    # Get log level from environment or use default
    if level is None:
        level_name = os.environ.get('NOCKSUP_LOG_LEVEL', 'INFO')
        level = getattr(logging, level_name.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates when reconfiguring
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Use the specified format or default
    formatter = logging.Formatter(format_str or DEFAULT_LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if requested
    if log_file:
        # Make sure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_timestamp():
    """Return a formatted timestamp for the current time."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

# Create default logger
logger = setup_logger('nocksup')
