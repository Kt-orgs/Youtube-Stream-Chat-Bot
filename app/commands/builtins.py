"""
Built-in commands for YouTube Chat Bot
"""

import os
from .command import BaseCommand, CommandContext
from typing import Optional


class HelpCommand(BaseCommand):
    """Display help information"""
    
    name = "help"
    aliases = ["h", "?", "commands"]
    description = "Display help for commands"
    usage = "!help [command_name] or !h or !? or !commands"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute help command"""
        args = self.parse_args(context.message)
        
        # If specific command requested
        if args:
            command_name = args[0].lower().lstrip("!")
            # This would need access to command parser
            # For now, return generic help
            return f"Help for !{command_name}: Use !help to see available commands"
        
        # Generic help - list all available commands
        help_text = "📜 Available commands:\n"
        help_text += "• !help, !commands - Show this help\n"
        help_text += "• !val <name#tag> - Get Valorant stats\n"
        help_text += "• !agent <name> - Get agent info\n"
        help_text += "• !map <name> - Get map info\n"
        help_text += "• !stats - Detailed stream stats\n"
        help_text += "• !viewers - Viewer breakdown\n"
        help_text += "• !top - Top chatters leaderboard\n"
        help_text += "• !botstats - Bot health metrics\n"
        help_text += "• !uptime - Stream uptime\n"
        help_text += "• !socials - Social links\n"
        help_text += "Try !help [command] for details!"
        return help_text


class PingCommand(BaseCommand):
    """Check if bot is responsive"""
    
    name = "ping"
    aliases = ["p", "online"]
    description = "Check if bot is online"
    usage = "!ping"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        return f"Pong! {context.author}, bot is live! 🎮"


class UptimeCommand(BaseCommand):
    """Show stream/bot uptime"""
    
    name = "uptime"
    aliases = ["up", "runtime"]
    description = "Show how long the stream has been live"
    usage = "!uptime"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        # This would integrate with YouTube API to get actual uptime
        # For now, return placeholder
        return "Stream uptime: The stream started a few minutes ago. Check back later for full stats!"


class SocialsCommand(BaseCommand):
    """Display streamer's social links"""
    
    name = "socials"
    aliases = ["links", "social", "follow"]
    description = "Show streamer's social media links"
    usage = "!socials or !links"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        # Use streamer profile if available
        profile = context.streamer_profile
        # Fall back to environment variables when profile is missing socials
        env_twitter = os.getenv("TWITTER_HANDLE")
        env_instagram = os.getenv("INSTAGRAM_HANDLE")
        env_discord = os.getenv("DISCORD_INVITE")
        env_twitch = os.getenv("TWITCH_URL")
        
        socials = []
        if profile.get("Twitter"):
            socials.append(f"Twitter: {profile['Twitter']}")
        elif env_twitter:
            socials.append(f"Twitter: {env_twitter}")
        if profile.get("Instagram"):
            socials.append(f"Instagram: {profile['Instagram']}")
        elif env_instagram:
            socials.append(f"Instagram: {env_instagram}")
        if profile.get("Discord"):
            socials.append(f"Discord: {profile['Discord']}")
        elif env_discord:
            socials.append(f"Discord: {env_discord}")
        if profile.get("Twitch"):
            socials.append(f"Twitch: {profile['Twitch']}")
        elif env_twitch:
            socials.append(f"Twitch: {env_twitch}")
        
        if socials:
            return "Follow the streamer: " + " | ".join(socials)
        else:
            return "No social links configured yet."


class StatusCommand(BaseCommand):
    """Show current stream status and statistics"""
    
    name = "stats"
    aliases = ["status", "stream"]
    description = "Show detailed stream statistics"
    usage = "!stats or !status"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute stats command with enhanced analytics"""
        try:
            try:
                from app.analytics import get_analytics_tracker
            except ModuleNotFoundError:
                from analytics import get_analytics_tracker
            
            # Get stream stats from YouTube API
            stats = context.youtube_api.get_stream_stats()
            
            if not stats:
                return "Unable to fetch stream stats right now"
            
            viewer_count = stats.get('viewer_count', 0)
            likes = stats.get('likes', 0)
            subs = stats.get('subs', 0)
            
            # Get analytics data
            analytics = get_analytics_tracker()
            session_stats = analytics.get_session_stats()
            
            response = f"📊 **Stream Stats:**\n"
            response += f"👥 Viewers: {viewer_count}"
            
            # Add peak viewers if available
            if session_stats and session_stats.get('peak_viewers', 0) > 0:
                peak = session_stats['peak_viewers']
                response += f" (Peak: {peak})"
            
            response += f"\n👍 Likes: {likes} | 📺 Subs: {subs}\n"
            
            # Add engagement info
            top_chatters = analytics.get_top_chatters(100)
            active_chatters = len(top_chatters)
            if viewer_count > 0:
                engagement = (active_chatters / viewer_count) * 100
                response += f"💬 Chat: {active_chatters} active ({engagement:.1f}% engagement)"
            
            return response
            
        except Exception as e:
            # Fallback to basic stats if analytics fails
            stats = context.youtube_api.get_stream_stats()
            if stats:
                return f"📊 Stream: {stats['viewer_count']} watching, {stats['likes']} likes, {stats['subs']} subs!"
            return "Unable to fetch stats"
        
        if game:
            return f"Currently playing: {game} 🎮"
        elif topic:
            return f"Current topic: {topic} 💬"
        else:
            return "Stream is live! 🎉"
