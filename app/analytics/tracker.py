"""
Analytics tracker for monitoring stream and bot metrics
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from .database import AnalyticsDatabase
from app.logger import get_logger

logger = get_logger(__name__)


class AnalyticsTracker:
    """Main analytics tracking class"""
    
    _instance: Optional['AnalyticsTracker'] = None
    
    def __init__(self, db_path: str = "data/analytics.db"):
        """
        Initialize analytics tracker
        
        Args:
            db_path: Path to SQLite database
        """
        self.db = AnalyticsDatabase(db_path)
        self.current_session_id: Optional[int] = None
        self.session_start_time: Optional[datetime] = None
        
        # In-memory counters for bot metrics
        self.messages_processed = 0
        self.commands_executed = 0
        self.total_response_time = 0.0
        self.api_calls_success = 0
        self.api_calls_total = 0
        
        logger.info("Analytics tracker initialized")
    
    def start_session(self, video_id: str, stream_title: str = "", game: str = "") -> int:
        """
        Start a new analytics session
        
        Args:
            video_id: YouTube video ID
            stream_title: Stream title
            game: Current game
            
        Returns:
            Session ID
        """
        self.current_session_id = self.db.create_session(video_id, stream_title, game)
        self.session_start_time = datetime.now()
        
        # Reset counters
        self.messages_processed = 0
        self.commands_executed = 0
        self.total_response_time = 0.0
        self.api_calls_success = 0
        self.api_calls_total = 0
        
        logger.info(f"Started analytics session {self.current_session_id}")
        return self.current_session_id
    
    def end_session(self):
        """End the current analytics session"""
        if self.current_session_id:
            self.db.end_session(self.current_session_id)
            logger.info(f"Ended analytics session {self.current_session_id}")
            self.current_session_id = None
    
    def track_message(self, message_id: str, author: str, author_channel_id: str,
                     message_text: str, is_command: bool = False, 
                     command_name: Optional[str] = None):
        """
        Track a chat message
        
        Args:
            message_id: Unique message ID
            author: Message author
            author_channel_id: Author's channel ID
            message_text: Message content
            is_command: Whether message is a command
            command_name: Command name if applicable
        """
        if not self.current_session_id:
            logger.warning("Cannot track message: no active session")
            return
        
        self.db.log_message(
            self.current_session_id,
            message_id,
            author,
            author_channel_id,
            message_text,
            is_command,
            command_name
        )
        
        self.messages_processed += 1
    
    def track_viewer_count(self, viewer_count: int, likes: int = 0):
        """
        Track current viewer count
        
        Args:
            viewer_count: Current viewer count
            likes: Current like count
        """
        if not self.current_session_id:
            logger.warning("Cannot track viewers: no active session")
            return
        
        self.db.log_viewer_snapshot(self.current_session_id, viewer_count, likes)
    
    def track_command_execution(self, command_name: str, success: bool, 
                               response_time: float):
        """
        Track command execution
        
        Args:
            command_name: Name of the command
            success: Whether command executed successfully
            response_time: Time taken to execute (seconds)
        """
        if not self.current_session_id:
            logger.warning("Cannot track command: no active session")
            return
        
        self.db.update_command_stats(
            self.current_session_id,
            command_name,
            success,
            response_time
        )
        
        self.commands_executed += 1
        self.total_response_time += response_time
    
    def track_api_call(self, success: bool):
        """
        Track API call success/failure
        
        Args:
            success: Whether API call succeeded
        """
        self.api_calls_total += 1
        if success:
            self.api_calls_success += 1
    
    def get_top_chatters(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top chatters for current session
        
        Args:
            limit: Number of top chatters to return
            
        Returns:
            List of top chatters with message counts
        """
        if not self.current_session_id:
            return []
        
        return self.db.get_top_chatters(self.current_session_id, limit)
    
    def get_session_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get current session statistics
        
        Returns:
            Session stats dictionary
        """
        if not self.current_session_id:
            return None
        
        return self.db.get_session_stats(self.current_session_id)
    
    def get_command_stats(self) -> List[Dict[str, Any]]:
        """
        Get command statistics for current session
        
        Returns:
            List of command stats
        """
        if not self.current_session_id:
            return []
        
        return self.db.get_command_stats(self.current_session_id)
    
    def get_bot_metrics(self) -> Dict[str, Any]:
        """
        Get current bot performance metrics
        
        Returns:
            Dictionary of bot metrics
        """
        uptime_seconds = 0
        if self.session_start_time:
            uptime_seconds = (datetime.now() - self.session_start_time).total_seconds()
        
        avg_response_time = 0.0
        if self.commands_executed > 0:
            avg_response_time = self.total_response_time / self.commands_executed
        
        api_success_rate = 0.0
        if self.api_calls_total > 0:
            api_success_rate = (self.api_calls_success / self.api_calls_total) * 100
        
        return {
            "uptime_seconds": uptime_seconds,
            "messages_processed": self.messages_processed,
            "commands_executed": self.commands_executed,
            "avg_response_time": avg_response_time,
            "api_success_rate": api_success_rate,
            "api_calls_total": self.api_calls_total,
            "api_calls_success": self.api_calls_success
        }
    
    def export_session_report(self) -> Optional[Dict[str, Any]]:
        """
        Export comprehensive session report
        
        Returns:
            Complete session report as dictionary
        """
        if not self.current_session_id:
            return None
        
        session_stats = self.get_session_stats()
        top_chatters = self.get_top_chatters(10)
        command_stats = self.get_command_stats()
        bot_metrics = self.get_bot_metrics()
        
        return {
            "session": session_stats,
            "top_chatters": top_chatters,
            "commands": command_stats,
            "bot_metrics": bot_metrics,
            "export_time": datetime.now().isoformat()
        }
    
    def close(self):
        """Close analytics tracker and database"""
        self.end_session()
        self.db.close()


# Singleton instance
_tracker_instance: Optional[AnalyticsTracker] = None


def get_analytics_tracker() -> AnalyticsTracker:
    """
    Get or create analytics tracker singleton
    
    Returns:
        AnalyticsTracker instance
    """
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = AnalyticsTracker()
    return _tracker_instance
