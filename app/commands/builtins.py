"""
Built-in commands for YouTube Chat Bot
"""

import os
import logging
from .command import BaseCommand, CommandContext
from typing import Optional

logger = logging.getLogger(__name__)


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
            return self._get_command_help(command_name)
        
        # Concise help - fit in YouTube's character limit
        help_text = (
            "🤖 **StreamNova Commands:**\n\n"
            "📋 General: !help, !ping, !uptime, !socials\n"
            "📊 Stats: !stats, !viewers, !top, !topchatters, !botstats, !export\n"
            "🎮 Valorant: !val [user#tag] [region], !agent [name], !map [name]\n"
            "📈 Growth: !setgoal, !setfollowers, !challenge, !challengeprogress, !cancelchallenge, !growthstats\n\n"
            "💡 Use !help [command] for details (e.g., !help val, !help stats)"
        )
        return help_text
    
    def _get_command_help(self, command_name: str) -> str:
        """Get detailed help for a specific command"""
        
        command_details = {
            "help": (
                "📋 **!help** - Get command information\n"
                "Aliases: !h, !?, !commands\n"
                "Usage: !help [command_name]\n\n"
                "Shows all available commands or detailed help for a specific command.\n"
                "Examples: !help, !help val, !help stats"
            ),
            
            "ping": (
                "🔔 **!ping** - Check bot responsiveness\n"
                "Aliases: !p, !online\n"
                "Usage: !ping\n\n"
                "Bot replies with 'Pong!' to confirm it's alive and responding.\n"
                "Use this if you're not sure if the bot is working."
            ),
            
            "uptime": (
                "⏱️ **!uptime** - Stream uptime\n"
                "Aliases: !up, !runtime\n"
                "Usage: !uptime\n\n"
                "Shows how long the stream has been live.\n"
                "Useful for tracking long streaming sessions!"
            ),
            
            "socials": (
                "📱 **!socials** - Streamer social links\n"
                "Aliases: !links, !follow, !social\n"
                "Usage: !socials\n\n"
                "Displays all streamer's social media:\n"
                "• Twitter/X\n"
                "• Instagram\n"
                "• Discord\n"
                "• Twitch\n"
                "Click the links to follow!"
            ),
            
            "stats": (
                "📊 **!stats** - Detailed stream statistics\n"
                "Aliases: !status, !stream\n"
                "Usage: !stats\n\n"
                "Shows comprehensive stream data:\n"
                "• Current viewer count with peak\n"
                "• Likes and subscriber count\n"
                "• Active chatters percentage (engagement rate)\n"
                "Great for checking how the stream is doing!"
            ),
            
            "viewers": (
                "👥 **!viewers** - Viewer statistics\n"
                "Aliases: !viewercount, !watching\n"
                "Usage: !viewers\n\n"
                "Shows:\n"
                "• Total viewers watching\n"
                "• Active chatters in the stream\n"
                "• Engagement rate percentage\n"
                "Quick way to see stream health!"
            ),
            
            "top": (
                "🏆 **!top** - Leaderboard this stream\n"
                "Aliases: !leaderboard, !chatters, !topchatter\n"
                "Usage: !top\n\n"
                "Shows the 5 most active chatters RIGHT NOW:\n"
                "🥇 1st place, 🥈 2nd place, 🥉 3rd place, etc.\n"
                "Great for recognizing active chat members!"
            ),
            
            "topchatters": (
                "📈 **!topchatters** - Leaderboard by date\n"
                "Aliases: !yesterdaytop, !topusers\n"
                "Usage: !topchatters [yesterday/today/YYYY-MM-DD]\n\n"
                "Shows top chatters from a specific date:\n"
                "• !topchatters yesterday - Yesterday's top 5\n"
                "• !topchatters today - Today's top 5\n"
                "• !topchatters 2025-12-25 - Specific date\n"
                "Perfect for analyzing different streams!"
            ),
            
            "botstats": (
                "🤖 **!botstats** - Bot performance metrics\n"
                "Aliases: !botinfo, !botmetrics\n"
                "Usage: !botstats\n\n"
                "Shows bot health:\n"
                "• Uptime (how long running)\n"
                "• Messages processed\n"
                "• Commands executed\n"
                "• Average response time\n"
                "• API success rate\n"
                "Check if bot is performing well!"
            ),
            
            "export": (
                "💾 **!export** - Export session analytics\n"
                "Aliases: !report, !sessionreport\n"
                "Usage: !export\n\n"
                "Exports complete session data to JSON file:\n"
                "• All statistics\n"
                "• Top chatters\n"
                "• Command usage\n"
                "• Bot performance metrics\n"
                "Saved in logs/session_reports/ folder"
            ),
            
            "val": (
                "⚔️ **!val** - Valorant player stats\n"
                "Aliases: !valorant, !stats\n"
                "Usage: !val [username#TAG] [region]\n"
                "Or: !val [stats/rank] [username#TAG] [region]\n\n"
                "Get Valorant stats for any player:\n"
                "• Rank (RR points, tier)\n"
                "• Recent game stats (K/D ratio)\n"
                "• Win rate\n\n"
                "Regions: na (NA), eu (EU), ap (Asia), latam, br (Brazil), kr (Korea)\n"
                "Examples:\n"
                "• !val ProPlayer#123 eu\n"
                "• !val stats ProPlayer#123\n"
                "• !val rank ProPlayer#456 na"
            ),
            
            "agent": (
                "🎯 **!agent** - Valorant agent info\n"
                "Aliases: !agents, !champions\n"
                "Usage: !agent [agent_name]\n"
                "Or: !agent list - Show all agents\n\n"
                "Learn about Valorant agents:\n"
                "Agents: Reyna, Jett, Phoenix, Sage, Omen, Brimstone,\n"
                "Cypher, Killjoy, Viper, Sova, Yoru, Astra,\n"
                "Skye, Chamber, Neon, Fade, Gekko, Harbor, Iso, Clove\n\n"
                "Examples:\n"
                "• !agent jett - Jett abilities\n"
                "• !agents - List all agents"
            ),
            
            "map": (
                "🗺️ **!map** - Valorant map info\n"
                "Aliases: !maps\n"
                "Usage: !map [map_name]\n"
                "Or: !map list - Show all maps\n\n"
                "Get Valorant map information:\n"
                "Maps: Ascent, Bind, Haven, Split, Icebox,\n"
                "Breeze, Fracture, Pearl, Sunset\n\n"
                "Examples:\n"
                "• !map ascent - Ascent strategies\n"
                "• !maps - List all maps"
            ),
            
            "setgoal": (
                "🎯 **!setgoal** - Set subscriber goal\n"
                "Aliases: !goal\n"
                "Usage: !setgoal [number]\n\n"
                "Set a channel growth goal:\n"
                "• Displays progress toward goal\n"
                "• Announced periodically in chat\n"
                "• Motivates community to help\n\n"
                "Example: !setgoal 2000\n"
                "Bot will announce: 'Need 157 more for 2000 goal!'"
            ),
            
            "setfollowers": (
                "👥 **!setfollowers** - Update follower count\n"
                "Aliases: !followers, !setcurrentfollowers\n"
                "Usage: !setfollowers [number]\n\n"
                "Manually update current follower count:\n"
                "• Updates progress toward goal\n"
                "• Shows remaining followers needed\n"
                "• Helps with growth tracking\n\n"
                "Example: !setfollowers 1234\n"
                "Bot calculates goal progress automatically"
            ),
            
            "challenge": (
                "🎯 **!challenge** - Start community challenge\n"
                "Aliases: !startchallenge\n"
                "Usage: !challenge [message_count] [reward]\n\n"
                "Create a fun community challenge:\n"
                "• Set message target for chat\n"
                "• Announce reward when goal reached\n"
                "• Great for engagement!\n\n"
                "Example: !challenge 500 I'll play a game with chat\n"
                "Bot: 'Challenge: If chat reaches 500 messages, I'll play a game!'"
            ),
            
            "challengeprogress": (
                "📊 **!challengeprogress** - Challenge progress\n"
                "Aliases: !cprogress\n"
                "Usage: !challengeprogress\n\n"
                "Check progress on active challenge:\n"
                "• Shows messages so far\n"
                "• Shows target\n"
                "• Shows percentage complete\n"
                "Great for hype during challenges!"
            ),
            
            "cancelchallenge": (
                "❌ **!cancelchallenge** - Cancel challenge\n"
                "Aliases: !stopchallenge\n"
                "Usage: !cancelchallenge\n\n"
                "Cancel the current active challenge:\n"
                "• Stops progress tracking\n"
                "• Clears challenge data\n"
                "• Can start new challenge after"
            ),
            
            "growthstats": (
                "📈 **!growthstats** - Growth statistics\n"
                "Aliases: !gstats\n"
                "Usage: !growthstats\n\n"
                "View channel growth metrics:\n"
                "• New viewers this stream\n"
                "• Active chatters\n"
                "• Most active chatter\n"
                "• Progress toward follower goal\n"
                "• Active challenge status"
            ),
        }
        
        # Return detailed help or generic message
        help_text = command_details.get(command_name.lower())
        
        if help_text:
            return help_text
        else:
            return (
                f"❌ Command '!{command_name}' not found.\n\n"
                f"Available command categories:\n"
                f"• !help general - General commands\n"
                f"• !help stats - Stream statistics\n"
                f"• !help val - Valorant commands\n"
                f"• !help growth - Growth commands\n\n"
                f"Or use !help to see all commands!"
            )


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
        
        # Debug logging
        logger.info(f"[SocialsCommand] Profile type: {type(profile)}")
        logger.info(f"[SocialsCommand] Profile keys: {list(profile.keys()) if profile else 'None'}")
        if profile:
            logger.info(f"[SocialsCommand] Twitter={profile.get('Twitter')}, Instagram={profile.get('Instagram')}, Discord={profile.get('Discord')}")
        
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
