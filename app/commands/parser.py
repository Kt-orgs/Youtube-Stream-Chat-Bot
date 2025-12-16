"""
Command parser for YouTube Chat Bot
Routes messages to appropriate command handlers
"""

import logging
from typing import Optional, List
from .command import BaseCommand, CommandContext
try:
    from app.logger import get_logger
except ModuleNotFoundError:
    from logger import get_logger

logger = get_logger(__name__)


class CommandParser:
    """Parses and routes chat messages to appropriate commands"""
    
    def __init__(self):
        """Initialize command parser with empty command registry"""
        self.commands: dict = {}  # command_name -> command_instance
        self.command_list: List[BaseCommand] = []
    
    def register(self, command: BaseCommand) -> None:
        """
        Register a command handler
        
        Args:
            command: Command instance to register
        """
        self.commands[command.name] = command
        self.command_list.append(command)
        
        # Register aliases
        for alias in command.aliases:
            self.commands[alias] = command
        
        logger.debug(f"Registered command: !{command.name}")
    
    def get_command(self, command_name: str) -> Optional[BaseCommand]:
        """
        Get a command by name or alias
        
        Args:
            command_name: Name or alias of command (without !)
            
        Returns:
            Command instance or None if not found
        """
        return self.commands.get(command_name)
    
    def is_command(self, message: str) -> bool:
        """
        Check if this message looks like a command format
        
        Args:
            message: Chat message to check
            
        Returns:
            True if message starts with !
        """
        return message.strip().startswith("!")
    
    def can_handle(self, message: str) -> bool:
        """
        Check if this message is a command
        
        Args:
            message: Chat message to check
            
        Returns:
            True if message starts with ! and matches a registered command
        """
        if not message.startswith("!"):
            return False
        
        # Check if any command can handle this
        for command in self.command_list:
            if command.can_handle(message):
                return True
        
        return False
    
    async def execute(self, message: str, context: CommandContext) -> Optional[str]:
        """
        Parse and execute a command
        
        Args:
            message: Chat message (should start with !)
            context: CommandContext with dependencies
            
        Returns:
            Response message or None if no response
        """
        if not message.startswith("!"):
            return None
        
        # Find matching command
        for command in self.command_list:
            if command.can_handle(message):
                try:
                    logger.debug(f"Executing command for {context.author}: {message[:50]}...")
                    response = await command.execute(context)
                    if response:
                        logger.debug(f"Command response: {response[:60]}...")
                    return response
                except Exception as e:
                    logger.error(f"Error executing command {command.name}: {e}", exc_info=True)
                    return f"Error executing command: {str(e)[:50]}"
        
        # No matching command
        logger.debug(f"Unknown command: {message.split()[0]}")
        return None
    
    def get_all_commands(self) -> List[BaseCommand]:
        """Get list of all registered commands"""
        # Remove duplicates (aliases)
        seen = set()
        unique_commands = []
        for cmd in self.command_list:
            if cmd.name not in seen:
                seen.add(cmd.name)
                unique_commands.append(cmd)
        return unique_commands
