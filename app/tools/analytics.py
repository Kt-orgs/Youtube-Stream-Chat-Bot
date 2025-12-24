"""
Analytics tools for the agent to query chat history and statistics
"""

from datetime import datetime, timedelta
from typing import Optional
from app.analytics import get_analytics_tracker
from app.logger import get_logger

logger = get_logger(__name__)


def get_chat_analytics(
    query_type: str,
    date: Optional[str] = None,
    limit: int = 5
) -> str:
    """
    Get chat analytics and statistics
    
    Args:
        query_type: Type of query. Options:
            - 'top_chatters_yesterday': Most active users yesterday
            - 'top_chatters_today': Most active users today
            - 'top_chatters_date': Most active users on specific date (requires date param)
            - 'recent_sessions': Recent stream sessions
        date: Date string in YYYY-MM-DD format (required for 'top_chatters_date')
        limit: Number of results to return (default 5)
    
    Returns:
        Formatted string with analytics results
    """
    try:
        analytics = get_analytics_tracker()
        
        if query_type == 'top_chatters_yesterday':
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            top_chatters = analytics.db.get_top_chatters_by_date(yesterday, limit)
            
            if not top_chatters:
                return f"No chat activity found for yesterday ({yesterday})"
            
            result = f"Most active chatters yesterday ({yesterday}):\n"
            for idx, chatter in enumerate(top_chatters, 1):
                result += f"{idx}. {chatter['author']} - {chatter['message_count']} messages\n"
            
            return result.strip()
        
        elif query_type == 'top_chatters_today':
            today = datetime.now().strftime("%Y-%m-%d")
            top_chatters = analytics.db.get_top_chatters_by_date(today, limit)
            
            if not top_chatters:
                return "No chat activity found for today yet"
            
            result = f"Most active chatters today ({today}):\n"
            for idx, chatter in enumerate(top_chatters, 1):
                result += f"{idx}. {chatter['author']} - {chatter['message_count']} messages\n"
            
            return result.strip()
        
        elif query_type == 'top_chatters_date':
            if not date:
                return "Error: date parameter required for 'top_chatters_date' query"
            
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return f"Invalid date format: {date}. Use YYYY-MM-DD"
            
            top_chatters = analytics.db.get_top_chatters_by_date(date, limit)
            
            if not top_chatters:
                return f"No chat activity found for {date}"
            
            result = f"Most active chatters on {date}:\n"
            for idx, chatter in enumerate(top_chatters, 1):
                result += f"{idx}. {chatter['author']} - {chatter['message_count']} messages\n"
            
            return result.strip()
        
        elif query_type == 'recent_sessions':
            sessions = analytics.db.get_recent_sessions(days=7)
            
            if not sessions:
                return "No recent stream sessions found"
            
            result = "Recent stream sessions:\n"
            for session in sessions[:limit]:
                start = session['start_time']
                title = session['stream_title'] or "Untitled Stream"
                messages = session['total_messages']
                commands = session['total_commands']
                viewers = session['peak_viewers']
                
                result += f"• {start} - {title}\n"
                result += f"  {messages} messages, {commands} commands, peak {viewers} viewers\n"
            
            return result.strip()
        
        else:
            return f"Unknown query_type: {query_type}. Valid options: top_chatters_yesterday, top_chatters_today, top_chatters_date, recent_sessions"
    
    except Exception as e:
        logger.error(f"Error in get_chat_analytics: {e}", exc_info=True)
        return f"Error fetching analytics: {str(e)}"
