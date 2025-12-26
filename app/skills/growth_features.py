"""
Growth Features for YouTube Chat Bot
Includes: New viewer welcome, follower goals, community challenges, viewer callouts
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from app.logger import get_logger
except ImportError:
    from logger import get_logger

logger = get_logger(__name__)


class GrowthFeatures:
    """Manages growth-focused features for stream engagement"""
    
    CONFIG_FILE = "growth_config.json"
    
    def __init__(self):
        self.new_viewers = set()  # Track first-time chatters
        self.active_viewers = defaultdict(int)  # Track viewer message counts
        self.last_viewer_callout = 0  # Track last callout time
        self.last_follower_announcement = 0  # Track last follower announcement
        self.challenge_active = False
        self.challenge_config = {}
        self.follower_goal = 2000  # Default goal
        self.current_followers = 0
        
        # Load configuration if it exists
        self.load_config()
        
    def load_config(self):
        """Load growth features configuration"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.follower_goal = config.get('follower_goal', 2000)
                    self.challenge_config = config.get('challenge', {})
                    self.new_viewers = set(config.get('new_viewers', []))
                    logger.info(f"Loaded growth config: goal={self.follower_goal}")
            except Exception as e:
                logger.error(f"Error loading growth config: {e}")
    
    def save_config(self):
        """Save growth features configuration"""
        try:
            config = {
                'follower_goal': self.follower_goal,
                'challenge': self.challenge_config,
                'new_viewers': list(self.new_viewers)
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving growth config: {e}")
    
    def set_follower_goal(self, goal: int):
        """Set the follower goal target"""
        self.follower_goal = goal
        self.save_config()
        logger.info(f"Follower goal set to {goal}")
    
    def update_follower_count(self, current_followers: int):
        """Update current follower count"""
        self.current_followers = current_followers
    
    def is_new_viewer(self, username: str) -> bool:
        """Check if viewer is chatting for first time"""
        is_new = username not in self.new_viewers
        if is_new:
            self.new_viewers.add(username)
            self.save_config()
            logger.info(f"New viewer detected: {username}")
        return is_new
    
    def track_message(self, username: str):
        """Track viewer message for activity purposes"""
        self.active_viewers[username] += 1
    
    def get_new_viewer_welcome(self, username: str) -> str:
        """Generate welcome message for new viewers"""
        welcome_messages = [
            f"🎉 Welcome to the stream {username}! Glad to have you here! This is your first time chatting - hope you enjoy! 💙",
            f"👋 Hey {username}! Welcome to the community! First time here? You're gonna love this! 🔥",
            f"🌟 Welcome {username}! Fresh face in chat - let's make this awesome! 💪",
            f"🚀 {username} just joined the chat for the first time! Welcome aboard! 🎮",
        ]
        import random
        return random.choice(welcome_messages)
    
    def get_follower_progress(self) -> str:
        """Get follower goal progress message"""
        if self.current_followers >= self.follower_goal:
            return f"🎉 LOKI just hit {self.current_followers} followers! Thanks to everyone for the support! 💙"
        
        remaining = self.follower_goal - self.current_followers
        percentage = (self.current_followers / self.follower_goal) * 100
        
        return f"📈 LOKI is {remaining} followers away from {self.follower_goal}! Let's help reach the goal! ({percentage:.1f}%)"
    
    def set_challenge(self, message_target: int, reward_text: str):
        """Set a community challenge"""
        self.challenge_config = {
            'active': True,
            'message_target': message_target,
            'reward_text': reward_text,
            'start_time': time.time(),
            'start_message_count': sum(self.active_viewers.values())
        }
        self.challenge_active = True
        self.save_config()
        logger.info(f"Challenge set: {message_target} messages for '{reward_text}'")
        return f"🎯 Community Challenge: If chat reaches {message_target} messages, {reward_text}! Let's go! 🔥"
    
    def check_challenge_progress(self, current_message_count: int) -> str:
        """Check if challenge is met"""
        if not self.challenge_active or not self.challenge_config:
            return None
        
        target = self.challenge_config.get('message_target', 0)
        start_count = self.challenge_config.get('start_message_count', 0)
        messages_so_far = current_message_count - start_count
        
        if messages_so_far >= target:
            reward = self.challenge_config.get('reward_text', 'something awesome')
            self.challenge_active = False
            self.save_config()
            return f"🎉 Challenge Complete! Chat reached {messages_so_far} messages! {reward}! 🎊"
        
        progress = (messages_so_far / target) * 100
        remaining = target - messages_so_far
        return f"📊 Challenge Progress: {messages_so_far}/{target} messages ({progress:.0f}%) - {remaining} more needed!"
    
    def get_active_viewer_callout(self) -> str:
        """Get callout for most active viewers"""
        if not self.active_viewers:
            return None
        
        # Get top 3 active viewers
        top_viewers = sorted(self.active_viewers.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if not top_viewers:
            return None
        
        if len(top_viewers) == 1:
            return f"🌟 Big shoutout to {top_viewers[0][0]} for being super active in chat! Keep it up! 💪"
        elif len(top_viewers) == 2:
            return f"🌟 Shoutout to {top_viewers[0][0]} and {top_viewers[1][0]} for keeping chat alive! 💙"
        else:
            return f"🌟 Huge thanks to {top_viewers[0][0]}, {top_viewers[1][0]}, and {top_viewers[2][0]} for being amazing! 💪"
    
    def should_do_viewer_callout(self, callout_interval_minutes: int = 30) -> bool:
        """Check if enough time has passed for viewer callout"""
        now = time.time()
        interval_seconds = callout_interval_minutes * 60
        
        if now - self.last_viewer_callout >= interval_seconds:
            self.last_viewer_callout = now
            return True
        return False
    
    def should_announce_follower_progress(self, announcement_interval_minutes: int = 60) -> bool:
        """Check if enough time has passed for follower announcement"""
        now = time.time()
        interval_seconds = announcement_interval_minutes * 60
        
        if now - self.last_follower_announcement >= interval_seconds:
            self.last_follower_announcement = now
            return True
        return False
    
    def get_stats_summary(self) -> dict:
        """Get summary of growth stats"""
        return {
            'new_viewers_count': len(self.new_viewers),
            'active_viewers_count': len(self.active_viewers),
            'top_viewer': max(self.active_viewers.items(), key=lambda x: x[1])[0] if self.active_viewers else None,
            'follower_goal': self.follower_goal,
            'current_followers': self.current_followers,
            'followers_remaining': max(0, self.follower_goal - self.current_followers),
            'challenge_active': self.challenge_active
        }


# Global instance
_growth_features = None

def get_growth_features():
    """Get or create global growth features instance"""
    global _growth_features
    if _growth_features is None:
        _growth_features = GrowthFeatures()
    return _growth_features
