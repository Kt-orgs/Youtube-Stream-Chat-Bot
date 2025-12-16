"""
Configuration validation for startup
"""

import os
import logging
import re
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def validate_api_keys():
    """Validate that required API keys are present"""
    load_dotenv()
    
    errors = []
    warnings = []
    
    # YouTube API Key
    youtube_key = os.getenv('YOUTUBE_API_KEY')
    if not youtube_key:
        errors.append("❌ YOUTUBE_API_KEY not found in .env")
    else:
        logger.info("✅ YOUTUBE_API_KEY found")
    
    # Google API Key (Gemini)
    google_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GENAI_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not google_key:
        warnings.append("⚠️  No Gemini API key found (GOOGLE_API_KEY/GENAI_API_KEY/GEMINI_API_KEY). Agent will be disabled.")
    else:
        logger.info("✅ Gemini API key found")
    
    # Valorant API Key
    henrik_key = os.getenv('HENRIK_DEV_API_KEY')
    if not henrik_key:
        warnings.append("⚠️  HENRIK_DEV_API_KEY not found. Valorant stats will be unavailable.")
    else:
        logger.info("✅ HENRIK_DEV_API_KEY found")
    
    return errors, warnings

def validate_valorant_id(valorant_id: str) -> bool:
    """
    Validate Valorant ID format (Name#Tag)
    
    Args:
        valorant_id: Valorant ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not valorant_id or "#" not in valorant_id:
        return False
    
    pattern = r'^[a-zA-Z0-9]{1,16}#[a-zA-Z0-9]{1,5}$'
    return bool(re.match(pattern, valorant_id))

def validate_startup():
    """
    Perform all startup validation checks
    
    Returns:
        Tuple of (is_valid: bool, errors: list, warnings: list)
    """
    errors, warnings = validate_api_keys()
    
    if errors:
        logger.error("Configuration errors found:")
        for error in errors:
            logger.error(f"  {error}")
        return False, errors, warnings
    
    if warnings:
        logger.warning("Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  {warning}")
    
    logger.info("✅ Configuration validation passed")
    return True, errors, warnings

def validate_file_structure():
    """
    Validate that required directories and files exist or can be created
    """
    from pathlib import Path
    
    # Ensure directories exist
    dirs_to_check = [
        Path(__file__).parent / "data",
        Path(__file__).parent / "logs"
    ]
    
    for directory in dirs_to_check:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Directory exists or created: {directory}")
