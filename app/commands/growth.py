"""
Growth Features Commands
Commands for managing subscriber goals, community challenges, etc.
"""

from typing import Optional
from app.commands.command import BaseCommand, CommandContext

try:
    from app.logger import get_logger
    from app.skills.growth_features import get_growth_features
except ImportError:
    from logger import get_logger
    from skills.growth_features import get_growth_features

logger = get_logger(__name__)


class SetSubscriberGoalCommand(BaseCommand):
    """Set the subscriber goal target"""
    
    name = "setgoal"
    aliases = ["goal"]
    description = "Set subscriber goal (e.g., !setgoal 100)"
    usage = "!setgoal <number>"
    admin_only = True
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        if not context.message.startswith("!"):
            return None
        
        if not context.is_admin():
            logger.warning(f"Admin check failed for {context.author}: admin_users={context.admin_users}")
            return f"❌ Only admins can set subscriber goals! Current admins: {', '.join(context.admin_users)}"
        
        parts = context.message.split()
        if len(parts) < 2:
            return "Usage: !setgoal <number> (e.g., !setgoal 100)"
        
        try:
            goal = int(parts[1])
            if goal <= 0:
                return "Goal must be a positive number!"
            
            growth = get_growth_features()
            growth.set_subscriber_goal(goal)
            
            # Return the progress announcement immediately
            return growth.get_subscriber_progress()
        except ValueError:
            return f"'{parts[1]}' is not a valid number!"


class StartChallengeCommand(BaseCommand):
    """Start a community challenge"""
    
    name = "challenge"
    aliases = ["startchallenge"]
    description = "Start a community challenge (e.g., !challenge 500 do 50 pushups)"
    usage = "!challenge <message_count> <reward_text>"
    admin_only = True
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        if not context.message.startswith("!"):
            return None
        
        if not context.is_admin():
            logger.warning(f"Admin check failed for {context.author}: admin_users={context.admin_users}")
            return f"❌ Only admins can start challenges! Current admins: {', '.join(context.admin_users)}"
        
        parts = context.message.split(maxsplit=2)
        if len(parts) < 3:
            return "Usage: !challenge <message_count> <reward> (e.g., !challenge 500 play a raid)"
        
        try:
            message_target = int(parts[1])
            reward_text = parts[2]
            
            if message_target <= 0:
                return "Message count must be a positive number!"
            
            growth = get_growth_features()
            response = growth.set_challenge(message_target, reward_text)
            return response
        except ValueError:
            return f"'{parts[1]}' is not a valid number!"


class ViewGrowthStatsCommand(BaseCommand):
    """View growth stats"""
    
    name = "growthstats"
    aliases = ["gstats"]
    description = "View growth statistics"
    usage = "!growthstats"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        growth = get_growth_features()
        stats = growth.get_stats_summary()
        
        lines = [
            "📊 Growth Stats:",
            f"  New Viewers: {stats['new_viewers_count']}",
            f"  Active Chatters: {stats['active_viewers_count']}",
        ]
        
        if stats['top_viewer']:
            lines.append(f"  Top Chatter: {stats['top_viewer']}")
        
        lines.extend([
            f"  Subscriber Goal: {stats['subscribers_remaining']} more to {stats['subscriber_goal']}",
            f"  Challenge Active: {'Yes' if stats['challenge_active'] else 'No'}"
        ])
        
        return " | ".join(lines)


class ChallengeProgressCommand(BaseCommand):
    """Check challenge progress"""
    
    name = "challengeprogress"
    aliases = ["cprogress"]
    description = "Check current challenge progress"
    usage = "!challengeprogress"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        growth = get_growth_features()
        message_count = context.youtube_api.get_chat_message_count() if hasattr(context.youtube_api, 'get_chat_message_count') else 0
        
        progress = growth.check_challenge_progress(message_count)
        if progress:
            return progress
        return "No active challenge right now!"


class CancelChallengeCommand(BaseCommand):
    """Cancel current challenge"""
    
    name = "cancelchallenge"
    aliases = ["stopchallenge"]
    description = "Cancel the current challenge"
    usage = "!cancelchallenge"
    admin_only = True
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        if not context.is_admin():
            logger.warning(f"Admin check failed for {context.author}: admin_users={context.admin_users}")
            return f"❌ Only admins can cancel challenges! Current admins: {', '.join(context.admin_users)}"
        
        growth = get_growth_features()
        growth.challenge_active = False
        growth.save_config()
        return "Challenge cancelled!"


class SetCurrentSubscribersCommand(BaseCommand):
    """Set the current subscriber count"""
    
    name = "setsubs"
    aliases = ["subs", "setcurrentsubs", "setsubscribers"]
    description = "Set current subscriber count (e.g., !setsubs 60)"
    usage = "!setsubs <number>"
    admin_only = True
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        if not context.message.startswith("!"):
            return None
        
        if not context.is_admin():
            logger.warning(f"Admin check failed for {context.author}: admin_users={context.admin_users}")
            return f"❌ Only admins can set subscriber count! Current admins: {', '.join(context.admin_users)}"
        
        parts = context.message.split()
        if len(parts) < 2:
            return "Usage: !setsubs <number> (e.g., !setsubs 60)"
        
        try:
            subscribers = int(parts[1])
            if subscribers < 0:
                return "Subscribers must be a non-negative number!"
            
            growth = get_growth_features()
            growth.update_subscriber_count(subscribers)
            remaining = max(0, growth.subscriber_goal - subscribers)
            return f"👍 Current subscribers set to {subscribers}. {remaining} away from goal of {growth.subscriber_goal}!"
        except ValueError:
            return f"'{parts[1]}' is not a valid number!"
