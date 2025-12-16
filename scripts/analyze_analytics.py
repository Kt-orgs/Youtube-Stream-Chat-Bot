"""
Script to analyze analytics data from SQLite database
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = "data/analytics.db"


def connect_db():
    """Connect to analytics database"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def show_all_sessions():
    """List all recorded sessions"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, video_id, stream_title, game, start_time, end_time,
               peak_viewers, total_messages, total_commands
        FROM sessions
        ORDER BY start_time DESC
    """)
    
    sessions = cursor.fetchall()
    
    print("\n" + "="*80)
    print("ALL SESSIONS")
    print("="*80)
    
    for session in sessions:
        status = "🟢 Active" if session['is_active'] else "🔴 Ended"
        print(f"\nSession #{session['id']} {status}")
        print(f"  Video ID: {session['video_id']}")
        print(f"  Title: {session['stream_title'] or 'N/A'}")
        print(f"  Game: {session['game'] or 'N/A'}")
        print(f"  Started: {session['start_time']}")
        print(f"  Ended: {session['end_time'] or 'Still active'}")
        print(f"  Peak Viewers: {session['peak_viewers']}")
        print(f"  Messages: {session['total_messages']}")
        print(f"  Commands: {session['total_commands']}")
    
    conn.close()


def analyze_session(session_id):
    """Detailed analysis of a specific session"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Session info
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = cursor.fetchone()
    
    if not session:
        print(f"❌ Session {session_id} not found")
        conn.close()
        return
    
    print("\n" + "="*80)
    print(f"SESSION #{session_id} ANALYSIS")
    print("="*80)
    
    # Basic stats
    print(f"\n📊 Basic Stats:")
    print(f"  Video ID: {session['video_id']}")
    print(f"  Stream: {session['stream_title'] or 'N/A'}")
    print(f"  Game: {session['game'] or 'N/A'}")
    print(f"  Duration: {session['start_time']} to {session['end_time'] or 'Active'}")
    print(f"  Peak Viewers: {session['peak_viewers']}")
    print(f"  Total Messages: {session['total_messages']}")
    print(f"  Total Commands: {session['total_commands']}")
    
    # Top chatters
    cursor.execute("""
        SELECT author, COUNT(*) as msg_count
        FROM messages
        WHERE session_id = ?
        GROUP BY author
        ORDER BY msg_count DESC
        LIMIT 10
    """, (session_id,))
    
    top_chatters = cursor.fetchall()
    
    print(f"\n👥 Top 10 Chatters:")
    for idx, chatter in enumerate(top_chatters, 1):
        print(f"  {idx}. {chatter['author']}: {chatter['msg_count']} messages")
    
    # Command usage
    cursor.execute("""
        SELECT command_name, execution_count, success_count, 
               failure_count, avg_response_time
        FROM command_stats
        WHERE session_id = ?
        ORDER BY execution_count DESC
    """, (session_id,))
    
    commands = cursor.fetchall()
    
    if commands:
        print(f"\n⚡ Command Usage:")
        for cmd in commands:
            success_rate = (cmd['success_count'] / cmd['execution_count'] * 100) if cmd['execution_count'] > 0 else 0
            print(f"  !{cmd['command_name']}: {cmd['execution_count']} uses, "
                  f"{success_rate:.1f}% success, {cmd['avg_response_time']:.2f}s avg")
    
    # Viewer trends
    cursor.execute("""
        SELECT timestamp, viewer_count, likes
        FROM viewer_snapshots
        WHERE session_id = ?
        ORDER BY timestamp
    """, (session_id,))
    
    snapshots = cursor.fetchall()
    
    if snapshots:
        print(f"\n📈 Viewer Trends ({len(snapshots)} snapshots):")
        print(f"  Starting viewers: {snapshots[0]['viewer_count']}")
        print(f"  Peak viewers: {session['peak_viewers']}")
        if len(snapshots) > 1:
            print(f"  Ending viewers: {snapshots[-1]['viewer_count']}")
        print(f"  Final likes: {snapshots[-1]['likes'] if snapshots else 0}")
    
    conn.close()


def get_most_used_commands():
    """Get most used commands across all sessions"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT command_name, 
               SUM(execution_count) as total_uses,
               SUM(success_count) as total_success,
               AVG(avg_response_time) as avg_time
        FROM command_stats
        GROUP BY command_name
        ORDER BY total_uses DESC
    """)
    
    commands = cursor.fetchall()
    
    print("\n" + "="*80)
    print("MOST USED COMMANDS (All Time)")
    print("="*80)
    
    for cmd in commands:
        success_rate = (cmd['total_success'] / cmd['total_uses'] * 100) if cmd['total_uses'] > 0 else 0
        print(f"!{cmd['command_name']}: {cmd['total_uses']} uses, "
              f"{success_rate:.1f}% success, {cmd['avg_time']:.2f}s avg")
    
    conn.close()


def get_top_chatters_all_time():
    """Get top chatters across all sessions"""
    conn = connect_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT author, COUNT(*) as total_messages
        FROM messages
        GROUP BY author
        ORDER BY total_messages DESC
        LIMIT 20
    """)
    
    chatters = cursor.fetchall()
    
    print("\n" + "="*80)
    print("TOP CHATTERS (All Time)")
    print("="*80)
    
    for idx, chatter in enumerate(chatters, 1):
        print(f"{idx}. {chatter['author']}: {chatter['total_messages']} messages")
    
    conn.close()


def main():
    """Main menu"""
    while True:
        print("\n" + "="*80)
        print("ANALYTICS DASHBOARD")
        print("="*80)
        print("1. Show all sessions")
        print("2. Analyze specific session")
        print("3. Most used commands (all time)")
        print("4. Top chatters (all time)")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            show_all_sessions()
        elif choice == "2":
            session_id = input("Enter session ID: ").strip()
            try:
                analyze_session(int(session_id))
            except ValueError:
                print("❌ Invalid session ID")
        elif choice == "3":
            get_most_used_commands()
        elif choice == "4":
            get_top_chatters_all_time()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
