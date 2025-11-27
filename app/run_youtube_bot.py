"""
YouTube Live Chat Bot Runner
Main script to run the YouTube chat bot with ADK agent
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_integration.chat_bridge import run_youtube_chat_bot

# Use absolute path for profile file to ensure it's found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_FILE = os.path.join(BASE_DIR, "streamer_profile.json")

def get_streamer_profile():
    """Load or create streamer profile"""
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, 'r') as f:
                profile = json.load(f)
                
                # Backward compatibility check for Is Gaming
                if 'Is Gaming' not in profile:
                    print("\n[Update] Stream Configuration")
                    is_gaming = input("Is this a gaming stream? (yes/no): ").strip().lower().startswith('y')
                    profile['Is Gaming'] = is_gaming
                    
                    if is_gaming:
                        if 'Valorant ID' not in profile:
                            # Check if they play Valorant
                            game = input("What game do you primarily play? ").strip()
                            if 'valorant' in game.lower():
                                profile['Valorant ID'] = input("Enter your Valorant ID (Name#Tag): ").strip()
                                profile['Valorant Region'] = input("Enter your Valorant Region (ap, na, eu, kr, latam, br) [default: ap]: ").strip() or 'ap'
                    else:
                        if 'Stream Topic' not in profile:
                            profile['Stream Topic'] = input("What is your usual stream topic? ").strip()
                    
                    with open(PROFILE_FILE, 'w') as f_out:
                        json.dump(profile, f_out, indent=4)
                            
                print(f"Loaded streamer profile for: {profile.get('Name', 'Unknown')}")
                return profile
        except Exception as e:
            print(f"Error loading profile: {e}")
    
    print("\n" + "="*60)
    print("FIRST TIME SETUP - STREAMER PROFILE")
    print("="*60)
    print("Please answer a few questions to personalize the bot for you.")
    print("This information will be saved for future streams.\n")
    
    profile = {}
    
    # 1. Determine Stream Type
    is_gaming = input("Are you going to use this agent for a gaming stream? (yes/no): ").strip().lower().startswith('y')
    profile['Is Gaming'] = is_gaming
    
    # 2. Collect Type-Specific Info
    if is_gaming:
        game = input("Which game will you be playing? ").strip()
        if 'valorant' in game.lower():
            print("Valorant detected! Let's set up your stats.")
            profile['Valorant ID'] = input("What is your Valorant ID (Name#Tag)? (optional, press Enter to skip): ").strip()
            if profile['Valorant ID']:
                profile['Valorant Region'] = input("What is your Valorant Region (ap, na, eu, kr, latam, br) [default: ap]? ").strip() or 'ap'
    else:
        profile['Stream Topic'] = input("What will you be streaming? ").strip()
        
    # 3. General Info
    profile['Name'] = input("What is your name/streamer name? ").strip()
    profile['Location'] = input("Where are you from? (optional, press Enter to skip): ").strip()
    
    if is_gaming:
        profile['System Specs'] = input("What are your system specs (CPU/GPU/RAM)? (optional, press Enter to skip): ").strip()
        
    profile['Profession/Bio'] = input("What do you do (Bio)? (optional, press Enter to skip): ").strip()
    
    try:
        with open(PROFILE_FILE, 'w') as f:
            json.dump(profile, f, indent=4)
        print("\nProfile saved successfully!")
    except Exception as e:
        print(f"Error saving profile: {e}")
        
    return profile

def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment or prompt user
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    video_id = os.getenv('YOUTUBE_VIDEO_ID')
    agent_name = os.getenv('AGENT_NAME', 'youtube_chat_advanced')
    
    if not youtube_api_key:
        print("Error: YOUTUBE_API_KEY not found in .env file")
        print("Please add: YOUTUBE_API_KEY=your_key_here")
        return
    
    if not video_id:
        print("No YOUTUBE_VIDEO_ID found in .env")
        video_id = input("Enter your YouTube video ID: ").strip()
        
        if not video_id:
            print("Video ID is required")
            return
            
    # Get Streamer Profile
    streamer_profile = get_streamer_profile()
    
    # Get Current Context
    print("\n" + "-"*40)
    
    current_game = None
    stream_topic = None
    
    if streamer_profile.get('Is Gaming', True):
        current_game = input("What game are you playing today? ").strip()
    else:
        default_topic = streamer_profile.get('Stream Topic', '')
        stream_topic = input(f"What is the topic of today's stream? [{default_topic}]: ").strip() or default_topic
        
    print("-"*40 + "\n")
    
    print("=" * 60)
    print("YouTube Live Chat Bot")
    print("=" * 60)
    print(f"Video ID: {video_id}")
    print(f"Agent: {agent_name}")
    if current_game:
        print(f"Game: {current_game}")
    if stream_topic:
        print(f"Topic: {stream_topic}")
    print(f"Streamer: {streamer_profile.get('Name', 'Unknown')}")
    print("=" * 60)
    print("\nStarting bot... Press Ctrl+C to stop")
    print()
    
    # Run the bot
    try:
        asyncio.run(run_youtube_chat_bot(
            youtube_api_key=youtube_api_key,
            video_id=video_id,
            agent_name=agent_name,
            streamer_profile=streamer_profile,
            current_game=current_game,
            stream_topic=stream_topic
        ))
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
