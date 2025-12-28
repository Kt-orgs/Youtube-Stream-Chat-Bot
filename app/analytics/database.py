"""
SQLite database schema and operations for analytics
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.logger import get_logger

logger = get_logger(__name__)


class AnalyticsDatabase:
    """Manages SQLite database for analytics data"""
    
    def __init__(self, db_path: str = "data/analytics.db"):
        """
        Initialize analytics database
        
        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            cursor = self.connection.cursor()
            
            # Sessions table - tracks bot sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    video_id TEXT,
                    stream_title TEXT,
                    game TEXT,
                    peak_viewers INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    total_commands INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Messages table - tracks all chat messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    message_id TEXT UNIQUE,
                    author TEXT NOT NULL,
                    author_channel_id TEXT,
                    message_text TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    is_command BOOLEAN DEFAULT 0,
                    command_name TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Viewer snapshots - periodic viewer count tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS viewer_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    viewer_count INTEGER NOT NULL,
                    likes INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Command stats - aggregated command usage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    command_name TEXT NOT NULL,
                    execution_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(id),
                    UNIQUE(session_id, command_name)
                )
            """)
            
            # Bot metrics - performance tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    messages_processed INTEGER DEFAULT 0,
                    commands_executed INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    api_success_rate REAL DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_author 
                ON messages(author)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_viewer_snapshots_session 
                ON viewer_snapshots(session_id)
            """)
            
            self.connection.commit()
            logger.info(f"Analytics database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise
    
    def create_session(self, video_id: str, stream_title: str = "", game: str = "") -> int:
        """
        Create a new session
        
        Args:
            video_id: YouTube video ID
            stream_title: Stream title
            game: Current game being played
            
        Returns:
            Session ID
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO sessions (start_time, video_id, stream_title, game)
                VALUES (?, ?, ?, ?)
            """, (datetime.now(), video_id, stream_title, game))
            self.connection.commit()
            
            session_id = cursor.lastrowid
            logger.info(f"Created new session {session_id} for video {video_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}", exc_info=True)
            raise
    
    def end_session(self, session_id: int):
        """Mark session as ended"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE sessions 
                SET end_time = ?, is_active = 0
                WHERE id = ?
            """, (datetime.now(), session_id))
            self.connection.commit()
            logger.info(f"Ended session {session_id}")
            
        except Exception as e:
            logger.error(f"Error ending session: {e}", exc_info=True)
    
    def log_message(self, session_id: int, message_id: str, author: str,
                   author_channel_id: str, message_text: str, 
                   is_command: bool = False, command_name: str = None):
        """Log a chat message"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO messages 
                (session_id, message_id, author, author_channel_id, message_text, 
                 timestamp, is_command, command_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, message_id, author, author_channel_id, message_text,
                  datetime.now(), is_command, command_name))
            
            # Update session message count
            cursor.execute("""
                UPDATE sessions 
                SET total_messages = total_messages + 1
                WHERE id = ?
            """, (session_id,))
            
            self.connection.commit()
            
        except sqlite3.IntegrityError:
            # Duplicate message_id, skip
            pass
        except Exception as e:
            logger.error(f"Error logging message: {e}", exc_info=True)
    
    def log_viewer_snapshot(self, session_id: int, viewer_count: int, likes: int = 0):
        """Log viewer count snapshot"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO viewer_snapshots 
                (session_id, timestamp, viewer_count, likes)
                VALUES (?, ?, ?, ?)
            """, (session_id, datetime.now(), viewer_count, likes))
            
            # Update peak viewers if needed
            cursor.execute("""
                UPDATE sessions 
                SET peak_viewers = MAX(peak_viewers, ?)
                WHERE id = ?
            """, (viewer_count, session_id))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error logging viewer snapshot: {e}", exc_info=True)
    
    def update_command_stats(self, session_id: int, command_name: str, 
                            success: bool, response_time: float):
        """Update command execution statistics"""
        try:
            cursor = self.connection.cursor()
            
            # Check if record exists
            cursor.execute("""
                SELECT execution_count, success_count, failure_count, avg_response_time
                FROM command_stats
                WHERE session_id = ? AND command_name = ?
            """, (session_id, command_name))
            
            row = cursor.fetchone()
            
            if row:
                # Update existing record
                exec_count = row[0] + 1
                success_count = row[1] + (1 if success else 0)
                failure_count = row[2] + (0 if success else 1)
                # Running average
                new_avg = ((row[3] * row[0]) + response_time) / exec_count
                
                cursor.execute("""
                    UPDATE command_stats
                    SET execution_count = ?,
                        success_count = ?,
                        failure_count = ?,
                        avg_response_time = ?
                    WHERE session_id = ? AND command_name = ?
                """, (exec_count, success_count, failure_count, new_avg, 
                      session_id, command_name))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO command_stats
                    (session_id, command_name, execution_count, success_count, 
                     failure_count, avg_response_time)
                    VALUES (?, ?, 1, ?, ?, ?)
                """, (session_id, command_name, 1 if success else 0,
                      0 if success else 1, response_time))
            
            # Update session command count
            cursor.execute("""
                UPDATE sessions 
                SET total_commands = total_commands + 1
                WHERE id = ?
            """, (session_id,))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating command stats: {e}", exc_info=True)
    
    def get_top_chatters(self, session_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top chatters for a session"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT author, COUNT(*) as message_count
                FROM messages
                WHERE session_id = ?
                GROUP BY author
                ORDER BY message_count DESC
                LIMIT ?
            """, (session_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting top chatters: {e}", exc_info=True)
            return []
    
    def get_top_chatters_by_date(self, date_str: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top chatters for a specific date
        
        Args:
            date_str: Date in YYYY-MM-DD format (e.g., "2025-12-23")
            limit: Number of top chatters to return
            
        Returns:
            List of dicts with author and message_count
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT m.author, COUNT(*) as message_count
                FROM messages m
                JOIN sessions s ON m.session_id = s.id
                WHERE DATE(s.start_time) = ?
                GROUP BY m.author
                ORDER BY message_count DESC
                LIMIT ?
            """, (date_str, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting top chatters by date: {e}", exc_info=True)
            return []
    
    def get_recent_sessions(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent sessions from the past N days"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, start_time, end_time, stream_title, total_messages, 
                       total_commands, peak_viewers
                FROM sessions
                WHERE start_time >= datetime('now', '-' || ? || ' days')
                ORDER BY start_time DESC
            """, (days,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting recent sessions: {e}", exc_info=True)
            return []
    
    def get_yesterday_top_chatters(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top chatters from yesterday"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT m.author, COUNT(*) as message_count
                FROM messages m
                JOIN sessions s ON m.session_id = s.id
                WHERE DATE(s.start_time) = DATE('now', '-1 day')
                GROUP BY m.author
                ORDER BY message_count DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting yesterday's top chatters: {e}", exc_info=True)
            return []
    
    def get_session_stats(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive session statistics"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM sessions WHERE id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}", exc_info=True)
            return None
    
    def get_command_stats(self, session_id: int) -> List[Dict[str, Any]]:
        """Get command statistics for a session"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT command_name, execution_count, success_count, 
                       failure_count, avg_response_time
                FROM command_stats
                WHERE session_id = ?
                ORDER BY execution_count DESC
            """, (session_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting command stats: {e}", exc_info=True)
            return []
    
    def get_viewer_chat_history(self, author: str) -> List[Dict[str, Any]]:
        """
        Get all chat sessions for a specific viewer
        
        Args:
            author: Username of the viewer
            
        Returns:
            List of dicts with session info and message counts
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    s.id,
                    s.start_time,
                    s.stream_title,
                    s.game,
                    COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id AND m.author = ?
                WHERE m.author = ?
                GROUP BY s.id
                ORDER BY s.start_time DESC
            """, (author, author))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting viewer chat history for {author}: {e}", exc_info=True)
            return []
    
    def get_viewer_stats(self, author: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive stats for a viewer
        
        Args:
            author: Username of the viewer
            
        Returns:
            Dict with: first_chat_date, last_chat_date, total_messages, total_sessions
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    MIN(m.timestamp) as first_chat_date,
                    MAX(m.timestamp) as last_chat_date,
                    COUNT(m.id) as total_messages,
                    COUNT(DISTINCT m.session_id) as total_sessions
                FROM messages m
                WHERE m.author = ?
            """, (author,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting viewer stats for {author}: {e}", exc_info=True)
            return None
    
    def is_returning_viewer(self, author: str) -> bool:
        """
        Check if viewer has chatted in any past session (before current session)
        
        Args:
            author: Username of the viewer
            
        Returns:
            True if viewer has chatted before, False if new
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM messages
                WHERE author = ?
            """, (author,))
            
            row = cursor.fetchone()
            return row['count'] > 0 if row else False
            
        except Exception as e:
            logger.error(f"Error checking if viewer is returning: {e}", exc_info=True)
            return False
    
    def get_days_since_last_chat(self, author: str) -> Optional[int]:
        """
        Get number of days since viewer last chatted
        
        Args:
            author: Username of the viewer
            
        Returns:
            Number of days ago, or None if never chatted
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT CAST((julianday('now') - julianday(MAX(m.timestamp))) AS INTEGER) as days_ago
                FROM messages m
                WHERE m.author = ?
            """, (author,))
            
            row = cursor.fetchone()
            if row and row['days_ago'] is not None:
                return row['days_ago']
            return None
            
        except Exception as e:
            logger.error(f"Error getting days since last chat for {author}: {e}", exc_info=True)
            return None
    
    def get_most_recent_session_info(self, author: str) -> Optional[Dict[str, Any]]:
        """
        Get info about viewer's most recent session
        
        Args:
            author: Username of the viewer
            
        Returns:
            Dict with: session_id, start_time, stream_title, game, message_count
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    s.id,
                    s.start_time,
                    s.stream_title,
                    s.game,
                    COUNT(m.id) as message_count
                FROM sessions s
                JOIN messages m ON s.id = m.session_id AND m.author = ?
                WHERE m.author = ?
                GROUP BY s.id
                ORDER BY s.start_time DESC
                LIMIT 1
            """, (author, author))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting most recent session info for {author}: {e}", exc_info=True)
            return None
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Analytics database connection closed")
