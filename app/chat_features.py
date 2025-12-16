"""
Advanced chat features for YouTube Chat Bot
Includes rate limiting, spam detection, user engagement tracking
"""

import time
import logging
from typing import Dict, Optional
from collections import defaultdict
from app.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Simple rate limiter to prevent spam"""
    
    def __init__(self, calls_per_period: int = 1, period_seconds: int = 5):
        """
        Initialize rate limiter
        
        Args:
            calls_per_period: Max number of calls allowed
            period_seconds: Time period in seconds
        """
        self.calls_per_period = calls_per_period
        self.period_seconds = period_seconds
        self.calls: Dict[str, list] = defaultdict()  # user_id -> list of timestamps
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if action is allowed for user
        
        Args:
            user_id: Unique identifier for user
            
        Returns:
            True if action is allowed, False if rate limited
        """
        now = time.time()
        
        if user_id not in self.calls:
            self.calls[user_id] = []
        
        # Remove old calls outside the period
        self.calls[user_id] = [
            timestamp for timestamp in self.calls[user_id]
            if now - timestamp < self.period_seconds
        ]
        
        # Check if under limit
        if len(self.calls[user_id]) < self.calls_per_period:
            self.calls[user_id].append(now)
            return True
        
        return False
    
    def reset_user(self, user_id: str):
        """Reset rate limit for a specific user"""
        if user_id in self.calls:
            del self.calls[user_id]


class UserEngagementTracker:
    """Track user engagement metrics"""
    
    def __init__(self):
        self.user_messages: Dict[str, int] = defaultdict(int)
        self.user_first_seen: Dict[str, float] = {}
        self.user_last_seen: Dict[str, float] = {}
    
    def record_message(self, username: str) -> None:
        """Record a message from a user"""
        now = time.time()
        
        self.user_messages[username] += 1
        
        if username not in self.user_first_seen:
            self.user_first_seen[username] = now
        
        self.user_last_seen[username] = now
    
    def get_user_stats(self, username: str) -> dict:
        """Get engagement stats for a user"""
        return {
            "messages": self.user_messages.get(username, 0),
            "first_seen": self.user_first_seen.get(username),
            "last_seen": self.user_last_seen.get(username)
        }
    
    def get_top_users(self, limit: int = 10) -> list:
        """Get most active users"""
        sorted_users = sorted(
            self.user_messages.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [
            {
                "username": username,
                "messages": count,
                "stats": self.get_user_stats(username)
            }
            for username, count in sorted_users[:limit]
        ]


class SpamDetector:
    """Detect and filter spam messages"""
    
    # Spam patterns
    SPAM_PATTERNS = [
        "check out my channel",
        "subscribe to my channel",
        "click my link",
        "discord.gg",
        "twitch.tv",
        "youtube.com",
    ]
    
    # Repetition threshold
    REPETITION_THRESHOLD = 3  # Same message 3+ times
    
    def __init__(self):
        self.message_history: Dict[str, list] = defaultdict(list)
    
    def is_spam(self, username: str, message: str) -> bool:
        """
        Check if message is spam
        
        Args:
            username: Author of message
            message: Message text
            
        Returns:
            True if message appears to be spam
        """
        msg_lower = message.lower()
        
        # Check against known spam patterns
        for pattern in self.SPAM_PATTERNS:
            if pattern in msg_lower:
                logger.debug(f"Spam detected from {username}: {message[:30]}...")
                return True
        
        # Check for repetition
        if username in self.message_history:
            if message in self.message_history[username]:
                count = self.message_history[username].count(message)
                if count >= self.REPETITION_THRESHOLD:
                    logger.debug(f"Repetitive spam from {username}: {message[:30]}...")
                    return True
        
        # Store message
        self.message_history[username].append(message)
        # Keep only last 10 messages per user
        if len(self.message_history[username]) > 10:
            self.message_history[username].pop(0)
        
        return False
