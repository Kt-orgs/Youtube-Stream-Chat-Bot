"""
Growth Features for YouTube Chat Bot
Includes: New viewer welcome, subscriber goals, community challenges, viewer callouts
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
    
    @staticmethod
    def calculate_next_milestone(current_subs: int) -> int:
        """Calculate the next subscriber milestone based on current count
        
        Logic:
        - 0-60: next milestone is 100
        - 61-100: next milestone is 150
        - 101-150: next milestone is 200
        - 151+: round up to next 50 (e.g., 151→200, 201→250, etc.)
        """
        if current_subs <= 60:
            return 100
        elif current_subs <= 100:
            return 150
        elif current_subs <= 150:
            return 200
        else:
            # Round up to next 50
            return ((current_subs // 50) + 1) * 50
    
    def __init__(self, analytics_db=None):
        self.new_viewers = set()  # Track first-time chatters in current stream
        self.active_viewers = defaultdict(int)  # Track viewer message counts
        self.last_viewer_callout = 0  # Track last callout time
        self.last_subscriber_announcement = 0  # Track last subscriber announcement
        self.challenge_active = False
        self.challenge_config = {}
        self.subscriber_goal = 100  # Default goal
        self.current_subscribers = 0
        self.analytics_db = analytics_db  # Database reference for historical data
        
        # Load configuration if it exists
        self.load_config()
        
    def load_config(self):
        """Load growth features configuration"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Support both old 'follower' and new 'subscriber' keys for backwards compatibility
                    self.subscriber_goal = config.get('subscriber_goal', config.get('follower_goal', 100))
                    self.current_subscribers = config.get('current_subscribers', config.get('current_followers', 0))
                    self.challenge_config = config.get('challenge', {})
                    self.new_viewers = set(config.get('new_viewers', []))
                    logger.info(f"Loaded growth config: goal={self.subscriber_goal}, subscribers={self.current_subscribers}")
            except Exception as e:
                logger.error(f"Error loading growth config: {e}")
    
    def save_config(self):
        """Save growth features configuration"""
        try:
            config = {
                'subscriber_goal': self.subscriber_goal,
                'current_subscribers': self.current_subscribers,
                'challenge': self.challenge_config,
                'new_viewers': list(self.new_viewers)
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving growth config: {e}")
    
    def set_subscriber_goal(self, goal: int):
        """Set the subscriber goal target"""
        self.subscriber_goal = goal
        self.save_config()
        logger.info(f"Subscriber goal set to {goal}")
    
    def update_subscriber_count(self, current_subscribers: int, auto_set_goal: bool = True):
        """Update current subscriber count and optionally auto-set goal
        
        Args:
            current_subscribers: The current subscriber count
            auto_set_goal: If True, automatically calculate and set the next milestone goal
        """
        if current_subscribers > 0:
            old_count = self.current_subscribers
            self.current_subscribers = current_subscribers
            
            # Auto-set goal to next milestone if enabled and this is first time or count changed significantly
            if auto_set_goal and (old_count == 0 or abs(current_subscribers - old_count) >= 5):
                new_goal = self.calculate_next_milestone(current_subscribers)
                if new_goal != self.subscriber_goal:
                    self.subscriber_goal = new_goal
                    logger.info(f"Auto-set subscriber goal to {new_goal} based on current count {current_subscribers}")
            
            self.save_config()
            logger.info(f"Updated subscriber count to {current_subscribers}")
    
    def is_new_viewer(self, username: str) -> bool:
        """Check if viewer is chatting for first time in CURRENT stream"""
        is_new = username not in self.new_viewers
        if is_new:
            self.new_viewers.add(username)
            self.save_config()
            logger.info(f"New viewer detected (this stream): {username}")
        return is_new
    
    def is_returning_viewer(self, username: str) -> bool:
        """Check if viewer has chatted in PAST streams"""
        if not self.analytics_db:
            return False
        return self.analytics_db.is_returning_viewer(username)
    
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
    
    def get_returning_viewer_welcome(self, username: str) -> str:
        """Generate personalized welcome message for returning viewers"""
        if not self.analytics_db:
            return self.get_new_viewer_welcome(username)
        
        # Get viewer stats
        stats = self.analytics_db.get_viewer_stats(username)
        recent = self.analytics_db.get_most_recent_session_info(username)
        days_ago = self.analytics_db.get_days_since_last_chat(username)
        
        if not stats:
            return self.get_new_viewer_welcome(username)
        
        total_messages = stats.get('total_messages', 0)
        total_sessions = stats.get('total_sessions', 0)
        
        # Determine activity level
        activity_level = "legend" if total_messages > 100 else \
                        "super active" if total_messages > 50 else \
                        "pretty active" if total_messages > 20 else \
                        "familiar friend"
        
        # Create personalized message based on stats
        if days_ago == 0:
            # Today
            returning_messages = [
                f"🔥 {username} is back! Welcome back legend! You were super active today too! 💪",
                f"👋 {username}! Great to see you again today! You're on fire! 🎮",
            ]
        elif days_ago == 1:
            # Yesterday
            returning_messages = [
                f"🔥 {username} welcome back! We missed you! That was an epic stream yesterday! 💙",
                f"👋 {username}! Good to see you again! Remember yesterday? Great times! 🎮",
            ]
        elif days_ago <= 7:
            # Within a week
            returning_messages = [
                f"🔥 {username} welcome back! Been about {days_ago} days - glad you're back! Let's go! 💪",
                f"👋 {username}! Great to see you again! You were super active a few days ago! 🎮",
            ]
        else:
            # More than a week
            returning_messages = [
                f"🔥 {username} welcome back! Haven't seen you in {days_ago} days - we missed you! 💙",
                f"👋 {username}! You're back! Been a while ({days_ago} days) but you were a {activity_level} chatter! 🎮",
            ]
        
        # Add activity reference if impressive
        if total_messages > 50:
            returning_messages = [
                f"🔥 {username} is back! You've been super active with {total_messages}+ messages across {total_sessions} streams! Welcome back legend! 💪",
                f"👋 {username}! Welcome back! I remember you - you're one of our {activity_level} viewers! Great to see you! 🎮",
            ]
        
        import random
        return random.choice(returning_messages)
    
    def get_subscriber_progress(self) -> str:
        """Get subscriber goal progress message"""
        if self.current_subscribers >= self.subscriber_goal:
            return f"🎉 LOKI just hit {self.current_subscribers} subscribers! Thanks to everyone for the support! 💙"
        
        remaining = self.subscriber_goal - self.current_subscribers
        percentage = (self.current_subscribers / self.subscriber_goal) * 100
        
        return f"📈 LOKI is {remaining} subscribers away from {self.subscriber_goal}! Let's help reach the goal! ({percentage:.1f}%)"
    
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
    
    def get_active_viewer_callout(self, admin_users: list = None) -> str:
        """Get callout for most active viewers (excluding admins)
        
        Args:
            admin_users: List of admin usernames to exclude from shoutouts
        """
        if not self.active_viewers:
            return None
        
        # Filter out admin users from the list
        admin_users = admin_users or []
        filtered_viewers = {user: count for user, count in self.active_viewers.items() 
                          if user not in admin_users}
        
        if not filtered_viewers:
            return None
        
        # Get top 3 active viewers (excluding admins)
        top_viewers = sorted(filtered_viewers.items(), key=lambda x: x[1], reverse=True)[:3]
        
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
    
    def should_announce_subscriber_progress(self, announcement_interval_minutes: int = 60) -> bool:
        """Check if enough time has passed for subscriber announcement"""
        now = time.time()
        interval_seconds = announcement_interval_minutes * 60
        
        if now - self.last_subscriber_announcement >= interval_seconds:
            self.last_subscriber_announcement = now
            return True
        return False
    
    def get_stats_summary(self) -> dict:
        """Get summary of growth stats"""
        return {
            'new_viewers_count': len(self.new_viewers),
            'active_viewers_count': len(self.active_viewers),
            'top_viewer': max(self.active_viewers.items(), key=lambda x: x[1])[0] if self.active_viewers else None,
            'subscriber_goal': self.subscriber_goal,
            'current_subscribers': self.current_subscribers,
            'subscribers_remaining': max(0, self.subscriber_goal - self.current_subscribers),
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
