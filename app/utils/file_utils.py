"""
File I/O utilities with error handling
"""

import os
import logging
from app import constants

logger = logging.getLogger(__name__)

def ensure_data_dir():
    """Ensure data directory exists"""
    os.makedirs(constants.DATA_DIR, exist_ok=True)

def save_stats_to_file(content: str, file_path):
    """
    Save content to a file
    
    Args:
        content: Content to save
        file_path: Path to file (can be string or Path object)
    """
    try:
        # Convert Path object to string if needed
        file_path_str = str(file_path)
        
        # Ensure parent directory exists
        from pathlib import Path
        Path(file_path_str).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path_str, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug(f"Saved content to {file_path_str}: {content[:50]}")
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")

def save_message_id(message_id: str):
    """
    Save a processed message ID to file
    
    Args:
        message_id: The YouTube message ID to save
    """
    ensure_data_dir()
    
    try:
        with open(constants.PROCESSED_MESSAGES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{message_id}\n")
        logger.debug(f"Saved message ID: {message_id}")
    except Exception as e:
        logger.error(f"Error saving message ID: {e}")

def load_processed_messages() -> set:
    """
    Load processed message IDs from file
    
    Returns:
        Set of processed message IDs
    """
    ensure_data_dir()
    
    if os.path.exists(constants.PROCESSED_MESSAGES_FILE):
        try:
            with open(constants.PROCESSED_MESSAGES_FILE, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Error loading processed messages: {e}")
    return set()
