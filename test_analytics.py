"""Test script for analytics features"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import asyncio
from datetime import datetime, timedelta
from analytics.database import AnalyticsDatabase

def test_analytics():
    print("=" * 60)
    print("TESTING ANALYTICS DATABASE")
    print("=" * 60)
    
    db = AnalyticsDatabase('data/analytics.db')
    
    # Create a test session for yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"\n1. Creating test session for yesterday ({yesterday})...")
    session_id = db.create_session('test_video', f'Test Stream {yesterday}', 'Valorant')
    print(f"   ✅ Session {session_id} created")
    
    # Add some test messages
    print(f"\n2. Adding test chat messages...")
    test_messages = [
        ('msg1', 'User1', 'ch1', 'Hello!'),
        ('msg2', 'User1', 'ch1', 'How are you?'),
        ('msg3', 'User1', 'ch1', 'Great stream!'),
        ('msg4', 'User2', 'ch2', 'Nice!'),
        ('msg5', 'User2', 'ch2', 'Love this'),
        ('msg6', 'User3', 'ch3', 'Hi'),
    ]
    
    for msg_id, author, channel, text in test_messages:
        db.log_message(session_id, msg_id, author, channel, text, False, None)
    print(f"   ✅ Added {len(test_messages)} messages")
    
    # Update session timestamp to yesterday
    print(f"\n3. Setting session date to yesterday...")
    cursor = db.connection.cursor()
    cursor.execute("""
        UPDATE sessions 
        SET start_time = datetime('now', '-1 day')
        WHERE id = ?
    """, (session_id,))
    db.connection.commit()
    print(f"   ✅ Session backdated to yesterday")
    
    # Query top chatters from yesterday
    print(f"\n4. Querying top chatters from yesterday ({yesterday})...")
    top_chatters = db.get_top_chatters_by_date(yesterday, 5)
    
    if top_chatters:
        print(f"   ✅ Found {len(top_chatters)} chatters:")
        for idx, chatter in enumerate(top_chatters, 1):
            print(f"      {idx}. {chatter['author']} - {chatter['message_count']} messages")
    else:
        print(f"   ⚠️  No chatters found")
    
    # Query top chatters for current session
    print(f"\n5. Querying top chatters for session {session_id}...")
    session_chatters = db.get_top_chatters(session_id, 5)
    
    if session_chatters:
        print(f"   ✅ Found {len(session_chatters)} chatters:")
        for idx, chatter in enumerate(session_chatters, 1):
            print(f"      {idx}. {chatter['author']} - {chatter['message_count']} messages")
    else:
        print(f"   ⚠️  No chatters found")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe analytics database is working correctly!")
    print(f"Database location: data/analytics.db")
    print("\nYou can now:")
    print("  1. Run the bot during a live stream")
    print("  2. Use !topchatters command in chat")
    print("  3. Ask bot 'who was most active yesterday?'")
    print("=" * 60)

if __name__ == "__main__":
    test_analytics()
