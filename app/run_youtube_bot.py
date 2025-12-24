"""
YouTube Live Chat Bot Runner
Main script to run the YouTube chat bot with ADK agent
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Ensure imports work both when running from repo root and app folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import logging first
from logger import get_logger
from config_validator import validate_startup
from constants import STREAMER_PROFILE_FILE

logger = get_logger(__name__)

from youtube_integration.chat_bridge import run_youtube_chat_bot

# Use relative path for profile file
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
                                profile['Valorant Region'] = input("Enter your Valorant Region (ap, na, eu, kr, latam, br) [default: eu]: ").strip() or 'eu'
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
    # Check if running in non-interactive mode (e.g. GitHub Actions)
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print("Running in GitHub Actions - using default Valorant profile")
        is_gaming = True
        profile['Is Gaming'] = True
        profile['Name'] = os.environ.get('STREAMER_NAME', 'Streamer')
        profile['Valorant ID'] = os.environ.get('VALORANT_ID', '')
        profile['Valorant Region'] = os.environ.get('VALORANT_REGION', 'eu')
        profile['System Specs'] = "Cloud Bot"
        profile['Profession/Bio'] = "I am a bot running in the cloud!"
        
        # Save and return immediately
        try:
            with open(PROFILE_FILE, 'w') as f:
                json.dump(profile, f, indent=4)
            print("\nDefault profile saved successfully!")
            return profile
        except Exception as e:
            print(f"Error saving profile: {e}")
            return profile

    is_gaming = input("Are you going to use this agent for a gaming stream? (yes/no): ").strip().lower().startswith('y')
    profile['Is Gaming'] = is_gaming
    
    # 2. Collect Type-Specific Info
    if is_gaming:
        game = input("Which game will you be playing? ").strip()
        if 'valorant' in game.lower():
            print("Valorant detected! Let's set up your stats.")
            profile['Valorant ID'] = input("What is your Valorant ID (Name#Tag)? (optional, press Enter to skip): ").strip()
            if profile['Valorant ID']:
                profile['Valorant Region'] = input("What is your Valorant Region (ap, na, eu, kr, latam, br) [default: eu]? ").strip() or 'eu'
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
    # Validate configuration at startup
    is_valid, errors, warnings = validate_startup()
    if not is_valid:
        logger.error("Startup validation failed. Please fix the errors above.")
        return
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment or prompt user
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    video_id = os.getenv('YOUTUBE_VIDEO_ID')
    agent_name = os.getenv('AGENT_NAME', 'youtube_chat_advanced')
    # Optional: allow disabling LLM agent when key issues occur
    enable_agent = os.getenv('ENABLE_AGENT', 'true').strip().lower()

    # Surface Gemini key presence for troubleshooting (masked)
    google_api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GENAI_API_KEY') or os.getenv('GEMINI_API_KEY')
    if google_api_key:
        logger.info("Gemini key detected (env): ****" + google_api_key[-4:])
    else:
        logger.warning("No Gemini key found in env (GOOGLE_API_KEY/GENAI_API_KEY/GEMINI_API_KEY). Agent calls may fail.")
    if enable_agent not in ("1", "true", "yes", "y"):
        logger.info("Agent disabled via ENABLE_AGENT; running skills-only mode.")
    
    if not youtube_api_key:
        logger.error("Error: YOUTUBE_API_KEY not found in .env file")
        logger.error("Please add: YOUTUBE_API_KEY=your_key_here")
        return
    
    # Auto-detect live stream if video_id not provided
    if not video_id:
        logger.info("No YOUTUBE_VIDEO_ID in .env - attempting to auto-detect live stream...")
        try:
            from youtube_integration.youtube_api import YouTubeLiveChatAPI
            temp_api = YouTubeLiveChatAPI()
            temp_api.authenticate()
            video_id = temp_api.get_current_live_video_id()
            
            if not video_id:
                logger.error("Could not auto-detect live stream. Please ensure:")
                logger.error("  1. You have an active live stream running")
                logger.error("  2. Or provide YOUTUBE_VIDEO_ID in .env file")
                manual_id = input("\nEnter your YouTube video ID manually (or press Enter to exit): ").strip()
                if manual_id:
                    video_id = manual_id
                else:
                    return
            else:
                logger.info(f"✓ Auto-detected live stream with video ID: {video_id}")
        except Exception as e:
            logger.error(f"Error during auto-detection: {e}")
            logger.error("Please provide YOUTUBE_VIDEO_ID in .env file")
            return
    
    # Get Streamer Profile
    streamer_profile = get_streamer_profile()
    logger.info(f"Streamer profile loaded for: {streamer_profile.get('Name', 'Unknown')}")
    
    # Get Current Context
    logger.info("-" * 40)
    
    current_game = None
    stream_topic = None
    
    if streamer_profile.get('Is Gaming', True):
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            current_game = "Valorant"
        else:
            current_game = input("What game are you playing today? ").strip()
        logger.info(f"Game: {current_game}")
    else:
        default_topic = streamer_profile.get('Stream Topic', '')
        stream_topic = input(f"What is the topic of today's stream? [{default_topic}]: ").strip() or default_topic
        logger.info(f"Topic: {stream_topic}")
        
    logger.info("-" * 40)
    
    logger.info("=" * 60)
    logger.info("YouTube Live Chat Bot")
    logger.info("=" * 60)
    logger.info(f"Video ID: {video_id}")
    logger.info(f"Agent: {agent_name}")
    if current_game:
        logger.info(f"Game: {current_game}")
    if stream_topic:
        logger.info(f"Topic: {stream_topic}")
    logger.info(f"Streamer: {streamer_profile.get('Name', 'Unknown')}")
    logger.info("=" * 60)
    logger.info("\nStarting bot... Press Ctrl+C to stop")
    
    # Run the bot
    try:
        # Run continuously - GitHub Actions workflow will handle timeouts
        asyncio.run(run_youtube_chat_bot(
            video_id=video_id,
            agent_name=agent_name,
            streamer_profile=streamer_profile,
            current_game=current_game,
            stream_topic=stream_topic
        ))
        logger.info("\n\nBot completed - stream ended")
        return 0
    except KeyboardInterrupt:
        logger.info("\n\nBot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"\nError: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
