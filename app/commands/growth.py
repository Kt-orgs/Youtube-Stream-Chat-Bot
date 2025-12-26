"""
Growth Features Commands
Commands for managing follower goals, community challenges, etc.
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


class SetFollowerGoalCommand(BaseCommand):
    """Set the follower goal target"""
    
    name = "setgoal"
    aliases = ["goal"]
    description = "Set follower goal (e.g., !setgoal 2000)"
    usage = "!setgoal <number>"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        if not context.message.startswith("!"):
            return None
        
        parts = context.message.split()
        if len(parts) < 2:
            return "Usage: !setgoal <number> (e.g., !setgoal 2000)"
        
        try:
            goal = int(parts[1])
            if goal <= 0:
                return "Goal must be a positive number!"
            
            growth = get_growth_features()
            growth.set_follower_goal(goal)
            return f"📈 Follower goal set to {goal}! Let's reach it together! 💪"
        except ValueError:
            return f"'{parts[1]}' is not a valid number!"


class StartChallengeCommand(BaseCommand):
    """Start a community challenge"""
    
    name = "challenge"
    aliases = ["startchallenge"]
    description = "Start a community challenge (e.g., !challenge 500 do 50 pushups)"
    usage = "!challenge <message_count> <reward_text>"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        if not context.message.startswith("!"):
            return None
        
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
            f"  Follower Goal: {stats['followers_remaining']} more to {stats['follower_goal']}",
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
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute the command"""
        growth = get_growth_features()
        growth.challenge_active = False
        growth.save_config()
        return "Challenge cancelled!"
