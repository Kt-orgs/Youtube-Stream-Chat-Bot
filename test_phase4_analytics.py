"""
Test script for Phase 4 Analytics features
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analytics import get_analytics_tracker
from app.analytics.database import AnalyticsDatabase


async def test_analytics():
    """Test analytics functionality"""
    print("=" * 60)
    print("Phase 4 Analytics Test Suite")
    print("=" * 60)
    
    # Test 1: Database initialization
    print("\n[Test 1] Database Initialization...")
    try:
        db = AnalyticsDatabase("data/test_analytics.db")
        print("✅ Database created successfully")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return
    
    # Test 2: Create session
    print("\n[Test 2] Creating Analytics Session...")
    try:
        session_id = db.create_session("test_video_123", "Test Stream", "Valorant")
        print(f"✅ Session created: ID {session_id}")
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        return
    
    # Test 3: Log messages
    print("\n[Test 3] Logging Messages...")
    try:
        db.log_message(session_id, "msg1", "User1", "ch1", "Hello!", False, None)
        db.log_message(session_id, "msg2", "User2", "ch2", "!help", True, "help")
        db.log_message(session_id, "msg3", "User1", "ch1", "How are you?", False, None)
        db.log_message(session_id, "msg4", "User3", "ch3", "!stats", True, "stats")
        db.log_message(session_id, "msg5", "User1", "ch1", "Nice stream!", False, None)
        print("✅ 5 messages logged")
    except Exception as e:
        print(f"❌ Message logging failed: {e}")
        return
    
    # Test 4: Log viewer snapshots
    print("\n[Test 4] Logging Viewer Snapshots...")
    try:
        db.log_viewer_snapshot(session_id, 10, 5)
        db.log_viewer_snapshot(session_id, 15, 7)
        db.log_viewer_snapshot(session_id, 12, 6)
        print("✅ 3 viewer snapshots logged")
    except Exception as e:
        print(f"❌ Viewer snapshot logging failed: {e}")
        return
    
    # Test 5: Update command stats
    print("\n[Test 5] Updating Command Stats...")
    try:
        db.update_command_stats(session_id, "help", True, 0.15)
        db.update_command_stats(session_id, "stats", True, 0.25)
        db.update_command_stats(session_id, "val", True, 0.8)
        db.update_command_stats(session_id, "val", False, 0.5)
        print("✅ Command stats updated")
    except Exception as e:
        print(f"❌ Command stats update failed: {e}")
        return
    
    # Test 6: Get top chatters
    print("\n[Test 6] Retrieving Top Chatters...")
    try:
        top = db.get_top_chatters(session_id, 3)
        print(f"✅ Top chatters retrieved: {len(top)} users")
        for idx, chatter in enumerate(top, 1):
            print(f"   {idx}. {chatter['author']}: {chatter['message_count']} messages")
    except Exception as e:
        print(f"❌ Top chatters retrieval failed: {e}")
        return
    
    # Test 7: Get session stats
    print("\n[Test 7] Retrieving Session Stats...")
    try:
        stats = db.get_session_stats(session_id)
        print(f"✅ Session stats retrieved")
        print(f"   Total messages: {stats['total_messages']}")
        print(f"   Total commands: {stats['total_commands']}")
        print(f"   Peak viewers: {stats['peak_viewers']}")
    except Exception as e:
        print(f"❌ Session stats retrieval failed: {e}")
        return
    
    # Test 8: Get command stats
    print("\n[Test 8] Retrieving Command Stats...")
    try:
        cmd_stats = db.get_command_stats(session_id)
        print(f"✅ Command stats retrieved: {len(cmd_stats)} commands")
        for cmd in cmd_stats:
            print(f"   !{cmd['command_name']}: {cmd['execution_count']} executions, "
                  f"{cmd['success_count']} success, {cmd['avg_response_time']:.2f}s avg")
    except Exception as e:
        print(f"❌ Command stats retrieval failed: {e}")
        return
    
    # Test 9: Tracker integration
    print("\n[Test 9] Testing AnalyticsTracker...")
    try:
        tracker = get_analytics_tracker()
        tracker.start_session("test_video_456", "Test Stream 2", "CS:GO")
        tracker.track_message("m1", "TestUser", "ch1", "Test message", False, None)
        tracker.track_command_execution("help", True, 0.1)
        tracker.track_viewer_count(20, 10)
        
        metrics = tracker.get_bot_metrics()
        print("✅ Tracker working correctly")
        print(f"   Messages processed: {metrics['messages_processed']}")
        print(f"   Commands executed: {metrics['commands_executed']}")
        
        # Export report
        report = tracker.export_session_report()
        if report:
            print("✅ Session report exported successfully")
        
        tracker.end_session()
    except Exception as e:
        print(f"❌ Tracker test failed: {e}")
        return
    
    # Cleanup
    print("\n[Cleanup] Closing database...")
    db.close()
    print("✅ Database closed")
    
    print("\n" + "=" * 60)
    print("✅ All Phase 4 Analytics Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_analytics())
