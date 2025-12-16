"""
Logging configuration for YouTube Chat Bot
"""

import logging
import os
from datetime import datetime

# Ensure logs directory exists
LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Create log file with timestamp
log_filename = os.path.join(LOG_DIR, f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    """Get a logger instance with the given name"""
    return logging.getLogger(name)
