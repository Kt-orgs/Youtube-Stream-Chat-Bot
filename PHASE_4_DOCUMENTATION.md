# Phase 4: Analytics & Monitoring

## Overview

Phase 4 adds comprehensive analytics and monitoring capabilities to the YouTube Chat Bot. It tracks stream metrics, chat activity, command usage, and bot performance in real-time using a SQLite database.

---

## Features

### 📊 **Stream Analytics**
- Real-time viewer count tracking
- Peak viewer monitoring
- Chat engagement metrics
- Likes and subscriber tracking
- Historical data storage

### 👥 **Chat Analytics**
- Message tracking per user
- Active chatter identification
- Top chatters leaderboard
- Message frequency analysis
- Engagement rate calculation

### ⚡ **Command Analytics**
- Command execution tracking
- Success/failure rates
- Average response times
- Usage statistics per command
- Performance monitoring

### 🤖 **Bot Performance Metrics**
- Uptime tracking
- Total messages processed
- Total commands executed
- API call success rates
- Average response times

### 💾 **Data Persistence**
- SQLite database storage
- Session-based organization
- Historical data retention
- JSON export functionality

---

## New Commands

### `!stats` (Enhanced)
Shows detailed stream statistics with analytics data.

**Usage:** `!stats`

**Response includes:**
- Current viewer count
- Peak viewers (if available)
- Likes and subscribers
- Active chatters count
- Engagement percentage

**Example:**
```
📊 Stream Stats:
👥 Viewers: 45 (Peak: 67)
👍 Likes: 23 | 📺 Subs: 1,234
💬 Chat: 12 active (26.7% engagement)
```

---

### `!viewers`
Shows current viewer breakdown and engagement.

**Usage:** `!viewers`

**Response includes:**
- Total viewers watching
- Active chatters count
- Engagement rate

**Example:**
```
👥 45 viewers watching
💬 12 active chatters
📊 Engagement: 26.7%
```

---

### `!top` / `!leaderboard`
Shows the most active chatters for the current session.

**Usage:** `!top` or `!leaderboard`

**Aliases:** `!chatters`, `!topchatter`

**Response includes:**
- Top 5 chatters with medal rankings
- Message counts per user

**Example:**
```
🏆 Top Chatters:
🥇 Alice - 42 messages
🥈 Bob - 31 messages
🥉 Charlie - 28 messages
4️⃣ Diana - 15 messages
5️⃣ Eve - 12 messages
```

---

### `!botstats`
Shows bot health and performance metrics.

**Usage:** `!botstats`

**Aliases:** `!botinfo`, `!botmetrics`

**Response includes:**
- Bot uptime (formatted HH:MM:SS)
- Total messages processed
- Total commands executed
- Average response time
- API success rate

**Example:**
```
🤖 Bot Stats:
⏱️ Uptime: 2:34:15
💬 Messages: 487
⚡ Commands: 42
⚙️ Avg Response: 145ms
🌐 API Success: 98.5%
```

---

### `!export`
Exports current session analytics to a JSON file.

**Usage:** `!export`

**Aliases:** `!report`, `!sessionreport`

**Response includes:**
- Session summary
- File save confirmation
- Key metrics preview

**Example:**
```
📊 Session Report Exported!
💬 487 messages
⚡ 42 commands
👥 Peak: 67 viewers
📁 Saved: session_20251205_221530.json
```

**Export location:** `logs/session_reports/session_YYYYMMDD_HHMMSS.json`

---

## Database Schema

### Tables

#### `sessions`
Tracks bot sessions (one per stream).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| start_time | TIMESTAMP | Session start time |
| end_time | TIMESTAMP | Session end time (NULL if active) |
| video_id | TEXT | YouTube video ID |
| stream_title | TEXT | Stream title |
| game | TEXT | Game being played |
| peak_viewers | INTEGER | Peak concurrent viewers |
| total_messages | INTEGER | Total messages in session |
| total_commands | INTEGER | Total commands executed |
| is_active | BOOLEAN | Whether session is active |

#### `messages`
Tracks all chat messages.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| session_id | INTEGER | Foreign key to sessions |
| message_id | TEXT | Unique YouTube message ID |
| author | TEXT | Message author name |
| author_channel_id | TEXT | Author's channel ID |
| message_text | TEXT | Message content |
| timestamp | TIMESTAMP | Message timestamp |
| is_command | BOOLEAN | Whether message is a command |
| command_name | TEXT | Command name (if applicable) |

#### `viewer_snapshots`
Periodic viewer count tracking (every 60 seconds).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| session_id | INTEGER | Foreign key to sessions |
| timestamp | TIMESTAMP | Snapshot time |
| viewer_count | INTEGER | Viewer count at time |
| likes | INTEGER | Like count at time |

#### `command_stats`
Aggregated command execution statistics.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| session_id | INTEGER | Foreign key to sessions |
| command_name | TEXT | Command name |
| execution_count | INTEGER | Total executions |
| success_count | INTEGER | Successful executions |
| failure_count | INTEGER | Failed executions |
| avg_response_time | REAL | Average response time (seconds) |

#### `bot_metrics`
Bot performance metrics over time.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| session_id | INTEGER | Foreign key to sessions |
| timestamp | TIMESTAMP | Metric snapshot time |
| messages_processed | INTEGER | Messages processed |
| commands_executed | INTEGER | Commands executed |
| avg_response_time | REAL | Average response time |
| api_success_rate | REAL | API success rate (%) |

---

## Architecture

### Components

#### `AnalyticsDatabase` (`app/analytics/database.py`)
- Manages SQLite database operations
- Creates and maintains database schema
- Provides CRUD operations for all tables
- Handles data persistence and retrieval

**Key Methods:**
- `create_session()` - Start new analytics session
- `end_session()` - Mark session as ended
- `log_message()` - Record chat message
- `log_viewer_snapshot()` - Record viewer count
- `update_command_stats()` - Update command metrics
- `get_top_chatters()` - Retrieve top chatters
- `get_session_stats()` - Get session statistics

#### `AnalyticsTracker` (`app/analytics/tracker.py`)
- High-level analytics tracking interface
- Manages current session state
- Aggregates metrics in memory
- Provides singleton access pattern

**Key Methods:**
- `start_session()` - Begin tracking session
- `end_session()` - Stop tracking session
- `track_message()` - Track chat message
- `track_viewer_count()` - Track viewers
- `track_command_execution()` - Track command
- `track_api_call()` - Track API calls
- `get_bot_metrics()` - Get performance metrics
- `export_session_report()` - Export full report

#### Analytics Commands (`app/commands/analytics.py`)
- `ViewersCommand` - Viewer statistics
- `LeaderboardCommand` - Top chatters
- `BotStatsCommand` - Bot performance
- `ExportCommand` - Report export

### Integration

Analytics tracking is integrated into `YouTubeChatBridge`:

1. **Session Start:** Analytics session starts when bot connects
2. **Message Tracking:** Every chat message is logged
3. **Command Tracking:** Command execution time and success tracked
4. **Viewer Tracking:** Viewer count sampled every 60 seconds
5. **Session End:** Analytics session ends when bot stops

---

## Usage Guide

### Basic Usage

1. **Start the bot** - Analytics automatically begins tracking
2. **Use commands** - Query analytics in real-time via chat
3. **Export reports** - Save session data for later analysis
4. **Analyze data** - Use provided tools to explore metrics

### Real-Time Monitoring

Query live metrics directly from chat:
```
!stats      - Stream overview
!viewers    - Viewer breakdown
!top        - Top chatters
!botstats   - Bot health
```

### Post-Stream Analysis

#### Method 1: Interactive Dashboard
```powershell
python scripts/analyze_analytics.py
```

**Menu Options:**
1. **Show all sessions** - List all recorded streams
2. **Analyze specific session** - Detailed session breakdown
3. **Most used commands** - All-time command statistics
4. **Top chatters** - All-time leaderboard

#### Method 2: JSON Reports
Check `logs/session_reports/` for exported JSON files:
```json
{
  "session": {
    "id": 1,
    "video_id": "abc123",
    "start_time": "2025-12-05 20:00:00",
    "total_messages": 487,
    "peak_viewers": 67
  },
  "top_chatters": [
    {"author": "Alice", "message_count": 42},
    {"author": "Bob", "message_count": 31}
  ],
  "commands": [
    {
      "command_name": "val",
      "execution_count": 15,
      "avg_response_time": 0.82
    }
  ],
  "bot_metrics": {
    "uptime_seconds": 9255,
    "messages_processed": 487,
    "commands_executed": 42
  }
}
```

#### Method 3: Direct SQL Queries
```bash
sqlite3 data/analytics.db

# Example queries:
SELECT * FROM sessions;
SELECT author, COUNT(*) as msg_count 
FROM messages 
GROUP BY author 
ORDER BY msg_count DESC;

SELECT command_name, execution_count, avg_response_time 
FROM command_stats 
ORDER BY execution_count DESC;
```

---

## Custom Analysis Examples

### Find Most Active Streaming Hours
```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/analytics.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT strftime('%H', timestamp) as hour, 
           AVG(viewer_count) as avg_viewers
    FROM viewer_snapshots
    GROUP BY hour
    ORDER BY avg_viewers DESC
""")

for row in cursor.fetchall():
    print(f"Hour {row[0]}: {row[1]:.0f} avg viewers")
```

### Calculate Engagement Trends
```python
cursor.execute("""
    SELECT s.id, s.video_id,
           COUNT(DISTINCT m.author) as unique_chatters,
           s.peak_viewers,
           (COUNT(DISTINCT m.author) * 100.0 / s.peak_viewers) as engagement_rate
    FROM sessions s
    LEFT JOIN messages m ON s.id = m.session_id
    WHERE s.peak_viewers > 0
    GROUP BY s.id
    ORDER BY engagement_rate DESC
""")
```

### Find Command Response Time Trends
```python
cursor.execute("""
    SELECT command_name,
           AVG(avg_response_time) as avg_time,
           MIN(avg_response_time) as best_time,
           MAX(avg_response_time) as worst_time
    FROM command_stats
    GROUP BY command_name
    HAVING COUNT(*) > 5
    ORDER BY avg_time DESC
""")
```

---

## Configuration

### Viewer Snapshot Interval
Edit `chat_bridge.py` to change how often viewer counts are tracked:

```python
self.viewer_snapshot_interval = 60  # seconds (default: 60)
```

### Database Location
Edit database path in `AnalyticsDatabase` initialization:

```python
db = AnalyticsDatabase("data/analytics.db")  # default
db = AnalyticsDatabase("custom/path/analytics.db")  # custom
```

### Leaderboard Size
Modify `LeaderboardCommand` to show more/fewer chatters:

```python
top_chatters = analytics.get_top_chatters(5)  # default: 5
top_chatters = analytics.get_top_chatters(10)  # show top 10
```

---

## Performance Considerations

### Database Size
- **Messages:** ~500 bytes per message
- **Snapshots:** ~50 bytes per snapshot (every 60s)
- **Estimated:** ~50KB per hour for moderate chat

### Query Performance
- Indexes on `session_id`, `author` for fast queries
- `get_top_chatters()` optimized with GROUP BY
- Periodic cleanup recommended for old sessions

### Memory Usage
- In-memory counters are lightweight (~100 bytes)
- Database connections pooled efficiently
- No significant memory overhead

---

## Troubleshooting

### Database Lock Errors
If you see "database is locked" errors:
```python
# Increase timeout in database.py
self.connection = sqlite3.connect(self.db_path, timeout=30.0)
```

### Missing Data
If analytics shows zeros:
- Verify session started: Check `logs/bot_*.log`
- Confirm tracking enabled: Look for "Analytics session started"
- Check database: `sqlite3 data/analytics.db "SELECT * FROM sessions;"`

### Export Fails
If `!export` returns errors:
- Verify `logs/session_reports/` directory exists
- Check disk space
- Review logs for permission errors

---

## Future Enhancements

Potential additions for Phase 5+:
- **Web Dashboard:** Real-time charts and graphs
- **Advanced Analytics:** Sentiment analysis, trend detection
- **Automated Reports:** Daily/weekly summary emails
- **Multi-Stream Comparison:** Compare performance across streams
- **Viewer Retention:** Track returning vs new chatters
- **Command Suggestions:** Recommend popular commands to users

---

## Testing

Run the test suite to verify analytics functionality:

```powershell
python test_phase4_analytics.py
```

**Tests include:**
- ✅ Database initialization
- ✅ Session management
- ✅ Message logging
- ✅ Viewer tracking
- ✅ Command statistics
- ✅ Top chatters retrieval
- ✅ Report export

---

## API Reference

### AnalyticsTracker Methods

#### `start_session(video_id: str, stream_title: str, game: str) -> int`
Start new analytics session.

**Parameters:**
- `video_id`: YouTube video ID
- `stream_title`: Stream title
- `game`: Game being played

**Returns:** Session ID

#### `track_message(message_id, author, author_channel_id, message_text, is_command, command_name)`
Track a chat message.

#### `track_command_execution(command_name: str, success: bool, response_time: float)`
Track command execution with timing.

#### `get_bot_metrics() -> Dict[str, Any]`
Get current bot performance metrics.

**Returns:**
```python
{
    "uptime_seconds": 9255,
    "messages_processed": 487,
    "commands_executed": 42,
    "avg_response_time": 0.145,
    "api_success_rate": 98.5,
    "api_calls_total": 200,
    "api_calls_success": 197
}
```

---

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `app/analytics/__init__.py` | Module exports | 7 |
| `app/analytics/database.py` | Database operations | 360+ |
| `app/analytics/tracker.py` | Tracking logic | 250+ |
| `app/commands/analytics.py` | Analytics commands | 180+ |
| `scripts/analyze_analytics.py` | Analysis dashboard | 240+ |
| `test_phase4_analytics.py` | Test suite | 150+ |

**Total:** ~1,200 lines of code

---

## Summary

Phase 4 provides comprehensive analytics and monitoring for your YouTube Chat Bot:

✅ **Real-time tracking** of messages, commands, viewers  
✅ **Historical data** stored in SQLite database  
✅ **Live queries** via chat commands  
✅ **Post-stream analysis** with interactive tools  
✅ **Performance monitoring** for bot health  
✅ **Export capabilities** for custom analysis  

All data is automatically collected with zero configuration required!
