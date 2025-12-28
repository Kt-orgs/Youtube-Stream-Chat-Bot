"""
Analytics commands for stream and bot statistics
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from .command import BaseCommand, CommandContext
from app.logger import get_logger
from app.analytics import get_analytics_tracker

logger = get_logger(__name__)


class ViewersCommand(BaseCommand):
    """Show current viewer statistics"""
    
    name = "viewers"
    aliases = ["viewercount", "watching"]
    description = "Show current viewer count and breakdown"
    usage = "!viewers"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute viewers command"""
        try:
            # Get stream stats from YouTube API
            stats = context.youtube_api.get_stream_stats()
            
            if not stats:
                return "❌ Unable to fetch viewer stats right now"
            
            viewer_count = stats.get('viewer_count', 0)
            
            # Get active chatters from analytics
            analytics = get_analytics_tracker()
            top_chatters = analytics.get_top_chatters(100)  # Get all chatters
            active_chatters = len(top_chatters)
            
            # Calculate engagement rate
            engagement_rate = 0
            if viewer_count > 0:
                engagement_rate = (active_chatters / viewer_count) * 100
            
            response = f"👥 **{viewer_count}** viewers watching\n"
            response += f"💬 **{active_chatters}** active chatters\n"
            response += f"📊 Engagement: **{engagement_rate:.1f}%**"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in viewers command: {e}", exc_info=True)
            return "❌ Error fetching viewer stats"


class LeaderboardCommand(BaseCommand):
    """Show top chatters leaderboard"""
    
    name = "top"
    aliases = ["leaderboard", "chatters", "topchatter"]
    description = "Show most active chatters this stream"
    usage = "!top or !leaderboard"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute leaderboard command"""
        try:
            analytics = get_analytics_tracker()
            top_chatters = analytics.get_top_chatters(5)
            
            if not top_chatters:
                return "No chat activity yet this stream!"
            
            response = "🏆 **Top Chatters:**\n"
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            
            for idx, chatter in enumerate(top_chatters):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}."
                author = chatter['author']
                count = chatter['message_count']
                response += f"{medal} **{author}** - {count} messages\n"
            
            return response.rstrip()
            
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}", exc_info=True)
            return "❌ Error fetching leaderboard"


class TopChattersCommand(BaseCommand):
    """Show top chatters from yesterday or specific date"""
    
    name = "topchatters"
    aliases = ["yesterdaytop", "topusers"]
    description = "Show most active chatters from yesterday or specific date"
    usage = "!topchatters [yesterday|today|YYYY-MM-DD]"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute topchatters command"""
        try:
            analytics = get_analytics_tracker()
            args = context.message.strip().split()
            
            # Determine which date to query
            if len(args) > 1:
                date_arg = args[1].lower()
                if date_arg == "yesterday":
                    date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                    label = "Yesterday's"
                elif date_arg == "today":
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    label = "Today's"
                else:
                    # Try to parse as date
                    try:
                        datetime.strptime(date_arg, "%Y-%m-%d")
                        date_str = date_arg
                        label = f"{date_arg}"
                    except ValueError:
                        return "Invalid date format. Use: !topchatters [yesterday|today|YYYY-MM-DD]"
            else:
                # Default to yesterday
                date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                label = "Yesterday's"
            
            top_chatters = analytics.db.get_top_chatters_by_date(date_str, limit=5)
            
            if not top_chatters:
                return f"No chat activity found for {date_str}"
            
            response = f"🏆 **{label} Top Chatters:**\n"
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            
            for idx, chatter in enumerate(top_chatters):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}."
                author = chatter['author']
                count = chatter['message_count']
                response += f"{medal} **{author}** - {count} messages\n"
            
            return response.rstrip()
            
        except Exception as e:
            logger.error(f"Error in topchatters command: {e}", exc_info=True)
            return "❌ Error fetching top chatters"


class BotStatsCommand(BaseCommand):
    """Show bot performance statistics"""
    
    name = "botstats"
    aliases = ["botinfo", "botmetrics"]
    description = "Show bot health and performance metrics"
    usage = "!botstats"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute botstats command"""
        try:
            analytics = get_analytics_tracker()
            metrics = analytics.get_bot_metrics()
            
            # Format uptime
            uptime_seconds = int(metrics['uptime_seconds'])
            uptime_str = str(timedelta(seconds=uptime_seconds))
            
            # Format response time
            avg_response_ms = metrics['avg_response_time'] * 1000
            
            response = "🤖 **Bot Stats:**\n"
            response += f"⏱️ Uptime: {uptime_str}\n"
            response += f"💬 Messages: {metrics['messages_processed']}\n"
            response += f"⚡ Commands: {metrics['commands_executed']}\n"
            response += f"⚙️ Avg Response: {avg_response_ms:.0f}ms\n"
            
            if metrics['api_calls_total'] > 0:
                response += f"🌐 API Success: {metrics['api_success_rate']:.1f}%"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in botstats command: {e}", exc_info=True)
            return "❌ Error fetching bot stats"


class ExportCommand(BaseCommand):
    """Export session analytics report"""
    
    name = "export"
    aliases = ["report", "sessionreport"]
    description = "Export current session analytics to file"
    usage = "!export"
    admin_only = True
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute export command"""
        if not context.is_admin():
            logger.warning(f"Admin check failed for {context.author}: admin_users={context.admin_users}")
            return f"❌ Only admins can export analytics! Current admins: {', '.join(context.admin_users)}"
        
        try:
            analytics = get_analytics_tracker()
            report = analytics.export_session_report()
            
            if not report:
                return "❌ No active session to export"
            
            # Create reports directory if it doesn't exist
            reports_dir = "logs/session_reports"
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"session_{timestamp}.json"
            filepath = os.path.join(reports_dir, filename)
            
            # Write report to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Session report exported to {filepath}")
            
            # Generate summary
            session = report.get('session', {})
            total_messages = session.get('total_messages', 0)
            total_commands = session.get('total_commands', 0)
            peak_viewers = session.get('peak_viewers', 0)
            
            response = f"📊 **Session Report Exported!**\n"
            response += f"💬 {total_messages} messages\n"
            response += f"⚡ {total_commands} commands\n"
            response += f"👥 Peak: {peak_viewers} viewers\n"
            response += f"📁 Saved: {filename}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in export command: {e}", exc_info=True)
            return "❌ Error exporting report"
