"""
Base command class and command context
"""

import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
try:
    from app.logger import get_logger
except ModuleNotFoundError:
    from logger import get_logger

logger = get_logger(__name__)


class CommandContext:
    """Context passed to commands with necessary dependencies"""
    
    def __init__(self, 
                 author: str,
                 message: str,
                 youtube_api: Optional[Any] = None,
                 streamer_profile: Optional[Dict] = None,
                 current_game: Optional[str] = None,
                 stream_topic: Optional[str] = None,
                 admin_users: Optional[list] = None):
        """
        Initialize command context
        
        Args:
            author: Author of the command message
            message: Full message text
            youtube_api: YouTube API instance
            streamer_profile: Streamer profile dictionary
            current_game: Currently playing game
            stream_topic: Stream topic if not gaming
            admin_users: List of admin usernames (e.g., ['LokiVersee'])
        """
        import time
        self.author = author
        self.message = message
        self.youtube_api = youtube_api
        self.streamer_profile = streamer_profile or {}
        self.current_game = current_game
        self.stream_topic = stream_topic
        self.admin_users = admin_users or []
        self.timestamp = time.time()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like access to context"""
        return getattr(self, key, default)
    
    def is_admin(self) -> bool:
        """Check if the command author is an admin"""
        # Strip whitespace from author name for comparison
        author_clean = self.author.strip()
        
        # Check if author is in admin list (case-sensitive)
        is_admin = author_clean in self.admin_users
        
        if not is_admin:
            # Log debug info for troubleshooting
            logger.debug(f"Admin check: author='{author_clean}' (len={len(author_clean)}), admin_users={self.admin_users}")
        
        return is_admin


class BaseCommand(ABC):
    """Base class for all commands"""
    
    # Command name (e.g., "help", "stats", "uptime")
    name: str = ""
    
    # List of aliases (e.g., ["h", "?"] for help command)
    aliases: list = []
    
    # Short description
    description: str = ""
    
    # Usage example (e.g., "!stats [player_name]")
    usage: str = ""
    
    # Whether command requires specific permissions
    requires_auth: bool = False
    
    # Whether command requires admin privileges
    admin_only: bool = False
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def can_handle(self, message: str) -> bool:
        """
        Check if this command can handle the given message
        
        Args:
            message: Chat message to check
            
        Returns:
            True if this command should handle this message
        """
        msg_lower = message.lower().strip()
        
        # Check if message starts with command name or alias
        if msg_lower.startswith(f"!{self.name}"):
            return True
        
        for alias in self.aliases:
            if msg_lower.startswith(f"!{alias}"):
                return True
        
        return False
    
    def parse_args(self, message: str) -> list:
        """
        Extract arguments from message
        
        Args:
            message: Chat message
            
        Returns:
            List of arguments
        """
        # Remove command prefix and split by whitespace
        parts = message.strip().split()
        if parts:
            parts.pop(0)  # Remove command itself
        return parts
    
    @abstractmethod
    async def execute(self, context: CommandContext) -> Optional[str]:
        """
        Execute the command
        
        Args:
            context: CommandContext with message and dependencies
            
        Returns:
            Response message or None if no response needed
        """
        pass
    
    def get_help(self) -> str:
        """Get help text for this command"""
        help_text = f"**!{self.name}**"
        if self.aliases:
            help_text += f" (aliases: {', '.join(f'!{a}' for a in self.aliases)})"
        help_text += f"\n{self.description}"
        if self.usage:
            help_text += f"\nUsage: {self.usage}"
        return help_text
