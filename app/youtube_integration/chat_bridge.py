"""
YouTube Chat Bridge
Connects YouTube Live Chat to Google ADK Agent
"""

import asyncio
import time
import os
import logging
from collections import deque
from typing import Optional
import pytchat
from google.adk.agents import Agent
from google.adk import events
from .youtube_api import YouTubeLiveChatAPI
try:
    from app.skills import SkillRegistry, GreetingSkill, CommunityEngagementSkill, AICoHostSkill, FunnyHypeSkill, SmartGamingAssistantSkill, GrowthBoosterSkill
    from app.skills.growth_features import get_growth_features
    from app.constants import GREETING_WORDS, HYPE_TRIGGERS, SPECS_KEYWORDS, HELP_KEYWORDS, QUESTION_MARKERS
    from app.logger import get_logger
    from app.commands import (
        CommandParser, CommandContext,
        HelpCommand, PingCommand, UptimeCommand, SocialsCommand, StatusCommand,
        ValorantStatsCommand, ValorantAgentCommand, ValorantMapCommand,
        ViewersCommand, LeaderboardCommand, TopChattersCommand, BotStatsCommand, ExportCommand
    )
    from app.commands.growth import (
        SetSubscriberGoalCommand, StartChallengeCommand, ViewGrowthStatsCommand, 
        ChallengeProgressCommand, CancelChallengeCommand
    )
    from app.analytics import get_analytics_tracker
except ImportError:
    from skills import SkillRegistry, GreetingSkill, CommunityEngagementSkill, AICoHostSkill, FunnyHypeSkill, SmartGamingAssistantSkill, GrowthBoosterSkill
    from skills.growth_features import get_growth_features
    from constants import GREETING_WORDS, HYPE_TRIGGERS, SPECS_KEYWORDS, HELP_KEYWORDS, QUESTION_MARKERS
    from logger import get_logger
    from commands import (
        CommandParser, CommandContext,
        HelpCommand, PingCommand, UptimeCommand, SocialsCommand, StatusCommand,
        ValorantStatsCommand, ValorantAgentCommand, ValorantMapCommand,
        ViewersCommand, LeaderboardCommand, TopChattersCommand, BotStatsCommand, ExportCommand
    )
    from commands.growth import (
        SetSubscriberGoalCommand, StartChallengeCommand, ViewGrowthStatsCommand, 
        ChallengeProgressCommand, CancelChallengeCommand
    )
    from analytics import get_analytics_tracker

logger = get_logger(__name__)


class YouTubeChatBridge:
    """Bridge between YouTube Live Chat and ADK Agent"""
    
    def __init__(
        self,
        video_id: str,
        agent: Agent,
        streamer_profile: Optional[dict] = None,
        current_game: Optional[str] = None,
        stream_topic: Optional[str] = None,
        response_delay: float = 2.0,
        ignore_moderators: bool = False,
        ignore_owner: bool = False,
        require_mention: bool = False,
        bot_name: str = "StreamNova",
        bot_username: str = "StreamNova",
        admin_users: Optional[list] = None
    ):
        """
        Initialize the chat bridge
        
        Args:
            video_id: YouTube video ID of the live stream
            agent: The ADK Agent instance to use for generating responses
            streamer_profile: Dictionary containing streamer details
            current_game: Name of the game being played
            stream_topic: Topic of the stream (if not gaming)
            response_delay: Delay in seconds before responding (to avoid spam)
            ignore_moderators: If True, don't respond to moderator messages
            ignore_owner: If True, don't respond to channel owner messages
            require_mention: If True, bot only responds if directly mentioned (more conservative)
            bot_name: Name of the bot to use in messages (default: StreamNova)
            bot_username: Custom username/signature for bot messages (default: StreamNova)
            admin_users: List of admin usernames (e.g., ['LokiVersee'])
        """
        # Initialize API with OAuth support (for posting only)
        self.youtube = YouTubeLiveChatAPI()
        self.youtube.authenticate()
        logger.info(f"Initialized YouTube Chat Bridge for video {video_id}")
        
        self.agent = agent
        self.video_id = video_id
        self.response_delay = response_delay
        self.ignore_moderators = ignore_moderators
        self.ignore_owner = ignore_owner
        self.require_mention = require_mention  # More conservative response mode
        self.bot_name = bot_name  # Bot's unique name/persona
        self.bot_username = bot_username  # Customizable username signature for responses
        self.admin_users = admin_users or []  # Admin user list
        self.is_running = False

        # Store context for skills
        self.streamer_profile = streamer_profile or {}
        self.current_game = current_game
        self.stream_topic = stream_topic

        # Skills
        self.skills = SkillRegistry()
        # Register greeting first for quick welcome responses
        self.skills.register(GreetingSkill())
        self.skills.register(CommunityEngagementSkill({"min_gap_seconds": 180}))
        self.skills.register(AICoHostSkill())
        self.skills.register(FunnyHypeSkill())
        from app.skills import ValorantStatsSkill
        self.skills.register(ValorantStatsSkill())
        self.skills.register(SmartGamingAssistantSkill())
        self.skills.register(GrowthBoosterSkill({"min_gap_seconds": 180}))
        logger.debug(f"Registered {len(self.skills.list())} skills")
        
        # Initialize command parser with built-in and valorant commands
        self.command_parser = CommandParser()
        self.command_parser.register(HelpCommand())
        self.command_parser.register(PingCommand())
        self.command_parser.register(UptimeCommand())
        self.command_parser.register(SocialsCommand())
        self.command_parser.register(StatusCommand())
        self.command_parser.register(ValorantStatsCommand())
        self.command_parser.register(ValorantAgentCommand())
        self.command_parser.register(ValorantMapCommand())
        # Analytics commands
        self.command_parser.register(ViewersCommand())
        self.command_parser.register(LeaderboardCommand())
        self.command_parser.register(TopChattersCommand())
        self.command_parser.register(BotStatsCommand())
        self.command_parser.register(ExportCommand())
        # Growth features commands
        self.command_parser.register(SetSubscriberGoalCommand())
        self.command_parser.register(StartChallengeCommand())
        self.command_parser.register(ViewGrowthStatsCommand())
        self.command_parser.register(ChallengeProgressCommand())
        self.command_parser.register(CancelChallengeCommand())
        logger.debug(f"Registered {len(self.command_parser.get_all_commands())} commands")
        
        # Persistence for processed messages
        self.history_file = "processed_messages.txt"
        self.processed_messages = self.load_history()
        
        # Cache to store recent bot messages to avoid self-replies
        self.recent_bot_messages = deque(maxlen=50)
        
        # Helper: normalize text to compare bot messages regardless of formatting
        def _normalize_text(s: str) -> str:
            try:
                return ''.join(s.split()).lower().replace('*', '')
            except Exception:
                return s
        self._normalize_text = _normalize_text
        
        # Helper: append bot signature to responses
        def _append_bot_signature(message: str) -> str:
            """Append bot username signature to the message"""
            if not message:
                return message
            # Check if message is already too long after adding signature
            signature = f" - {self.bot_username}"
            total_length = len(message) + len(signature)
            if total_length > 200:
                # Truncate message to make room for signature
                available = 200 - len(signature)
                return message[:available].rstrip() + signature
            return message + signature
        self._append_bot_signature = _append_bot_signature
        
        # Analytics tracker
        self.analytics = get_analytics_tracker()
        self.viewer_snapshot_interval = 60  # Track viewers every 60 seconds
        self.last_viewer_snapshot = 0
        
        # Growth features - pass analytics database for historical viewer data
        self.growth = get_growth_features()
        self.growth.analytics_db = self.analytics.db  # Pass database reference for historical queries
        self.growth_feature_interval = 30  # Check growth features every 30 seconds
        self.last_growth_check = 0
        
        # Periodic announcement settings
        self.announcement_interval = 420  # 7 minutes in seconds
        self.last_announcement_time = 0
        self.messages_since_last_announcement = 0  # Track message count for smart announcements
        self.min_messages_for_announcement = 10  # Require at least 10 messages before announcing
        
    def _initialize_subscriber_count(self):
        """Initialize subscriber count from YouTube API on startup"""
        try:
            logger.info("Fetching initial subscriber count from YouTube...")
            stats = self.youtube.get_stream_stats(use_cache=False)
            if stats and stats.get('subs') and stats['subs'] > 0:
                self.growth.update_subscriber_count(stats['subs'])
                logger.info(f"Initialized subscriber count: {stats['subs']}")
            else:
                logger.warning("Could not fetch real-time subscriber count - check YouTube API permissions")
                # Check if we have a saved count from previous run
                if self.growth.current_subscribers > 0:
                    logger.info(f"Using previously saved subscriber count: {self.growth.current_subscribers}")
                else:
                    logger.warning("No subscriber count available - set manually with !setgoal command")
        except Exception as e:
            logger.error(f"Error initializing subscriber count: {e}")
        
    def load_history(self) -> set:
        """Load processed message IDs from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    messages = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(messages)} processed messages from history")
                return messages
            except Exception as e:
                logger.error(f"Error loading history: {e}")
        return set()

    def save_message_id(self, message_id: str):
        """Save a processed message ID to file"""
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(f"{message_id}\n")
        except Exception as e:
            logger.error(f"Error saving message ID: {e}")
        
    async def start(self):
        """Start the chat bridge"""
        logger.info(f"Starting YouTube Chat Bridge for video: {self.video_id}")
        
        # Get live chat ID (still needed for posting messages)
        chat_id = self.youtube.get_live_chat_id(self.video_id)
        
        if not chat_id:
            logger.error("Failed to get live chat ID. Make sure the video is live and has chat enabled.")
            return
        
        # Explicitly set the live_chat_id in the API object
        self.youtube.live_chat_id = chat_id
        logger.debug(f"Live chat ID set to: {chat_id}")
            
        # Determine environment; prefer pytchat to save quota, but fall back to API polling if it fails
        is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
        is_ci = os.environ.get('CI') == 'true'

        def build_api_chat_source():
            logger.warning("Using API polling for chat (quota will be consumed)")

            class YouTubeAPIChatSource:
                def __init__(self, youtube_api):
                    self.youtube = youtube_api
                    self.last_poll_time = 0
                    self.polling_interval = 10.0  # Start with 10s to be safe

                def is_alive(self):
                    return True

                def get(self):
                    return self

                def sync_items(self):
                    current_time = time.time()
                    if current_time - self.last_poll_time < self.polling_interval:
                        return []

                    self.last_poll_time = current_time
                    try:
                        messages, interval = self.youtube.fetch_chat_messages()
                        self.polling_interval = max(interval, 5.0)

                        result = []
                        for msg in messages:
                            class MessageObj:
                                pass

                            m = MessageObj()
                            m.id = msg['id']
                            m.message = msg['message']
                            m.datetime = msg['timestamp']

                            m.author = MessageObj()
                            m.author.name = msg['author']
                            m.author.channelId = msg['author_channel_id']
                            m.author.isChatModerator = msg['is_moderator']
                            m.author.isChatOwner = msg['is_owner']

                            result.append(m)
                        return result
                    except Exception as ex:
                        logger.error(f"Error fetching messages via API: {ex}")
                        return []

            return YouTubeAPIChatSource(self.youtube)

        # Try pytchat first (quota-free). If it fails anywhere, fall back to API polling.
        try:
            chat = pytchat.create(video_id=self.video_id)
            logger.info("Pytchat initialized successfully (Quota-free reading mode)")
        except Exception as e:
            logger.error(f"Error initializing pytchat: {e}")
            logger.info(f"Environment check - GITHUB_ACTIONS: {os.environ.get('GITHUB_ACTIONS')}, CI: {os.environ.get('CI')}")
            chat = build_api_chat_source()
        
        self.is_running = True
        logger.info("Chat bridge started successfully!")
        logger.info("Monitoring chat for messages...")
        
        # Start analytics session
        stream_title = self.stream_topic or self.current_game or "Unknown"
        game = self.current_game or ""
        self.analytics.start_session(self.video_id, stream_title, game)
        logger.info("Analytics session started")
        
        # Start intro message task (post after 60 seconds)
        async def post_intro_after_delay():
            try:
                await asyncio.sleep(60)  # Wait 60 seconds
                if not self.is_running:
                    return

                intro_msg = (
                    f"🤖 {self.bot_name} is here! Ask me anything by tagging me with @{self.bot_name}! Try !help, !stats, !ping, !uptime, !socials, !status"
                )
                try:
                    message_id = self.youtube.post_message(intro_msg)
                    if message_id:
                        self.recent_bot_messages.append(self._normalize_text(intro_msg))
                        self.processed_messages.add(message_id)
                        self.save_message_id(message_id)
                        logger.info(f"[BOT INTRO] Posted introduction message (ID: {message_id})")
                    else:
                        logger.warning("Failed to post intro message - message_id is None")
                except Exception as e:
                    err_text = str(e)
                    if "INVALID_REQUEST_METADATA" in err_text:
                        logger.warning("Intro message blocked by YouTube API (INVALID_REQUEST_METADATA). Skipping intro to avoid further errors.")
                    else:
                        logger.warning(f"Failed to post intro message: {e}")
            except asyncio.CancelledError:
                pass
        
        intro_task = asyncio.create_task(post_intro_after_delay())
        
        # QUOTA OPTIMIZATION: Periodic stats disabled - use !stats command instead
        # This saves ~600-4,800 units/day depending on frequency
        logger.info("[QUOTA SAVER] Periodic stats disabled. Use !stats command to get current stats.")
        
        # Track last stream status check
        last_stream_check = time.time()
        stream_check_interval = 60  # Check every 60 seconds
        
        # Main loop
        while self.is_running and chat.is_alive():
            try:
                # Check if stream is still active periodically
                current_time = time.time()
                if current_time - last_stream_check >= stream_check_interval:
                    if not self.youtube.is_stream_active(self.video_id):
                        logger.info("Stream has ended - stopping bot gracefully")
                        self.is_running = False
                        break
                    last_stream_check = current_time
                
                # Check for periodic growth feature announcements
                if current_time - self.last_growth_check >= self.growth_feature_interval:
                    self.last_growth_check = current_time
                    
                    # Check for subscriber goal progress announcement (every 30 minutes)
                    if self.growth.should_announce_subscriber_progress(announcement_interval_minutes=30):
                        progress_msg = self.growth.get_subscriber_progress()
                        try:
                            msg_id = self.youtube.post_message(progress_msg)
                            if msg_id:
                                self.processed_messages.add(msg_id)
                                self.save_message_id(msg_id)
                                self.recent_bot_messages.append(self._normalize_text(progress_msg))
                                logger.info(f"[SUBSCRIBER PROGRESS]: {progress_msg}")
                        except Exception as e:
                            logger.warning(f"Failed to post subscriber progress: {e}")
                    
                    # Check for viewer callout (excluding admins)
                    if self.growth.should_do_viewer_callout(callout_interval_minutes=30):
                        callout_msg = self.growth.get_active_viewer_callout(admin_users=self.admin_users)
                        if callout_msg:
                            try:
                                msg_id = self.youtube.post_message(callout_msg)
                                if msg_id:
                                    self.processed_messages.add(msg_id)
                                    self.save_message_id(msg_id)
                                    self.recent_bot_messages.append(self._normalize_text(callout_msg))
                                    logger.info(f"[VIEWER CALLOUT]: {callout_msg}")
                            except Exception as e:
                                logger.warning(f"Failed to post viewer callout: {e}")
                
                # Periodic announcement (every 7 minutes + at least 10 messages in chat)
                if current_time - self.last_announcement_time >= self.announcement_interval:
                    # Only announce if there's been chat activity (at least 10 messages)
                    if self.messages_since_last_announcement >= self.min_messages_for_announcement:
                        self.last_announcement_time = current_time
                        self.messages_since_last_announcement = 0  # Reset counter
                        announcement_msg = f"Hey everyone {self.bot_name} is here in the chat ask me anything by tagging me with @{self.bot_name}"
                        try:
                            msg_id = self.youtube.post_message(announcement_msg)
                            if msg_id:
                                self.processed_messages.add(msg_id)
                                self.save_message_id(msg_id)
                                self.recent_bot_messages.append(self._normalize_text(announcement_msg))
                                logger.info(f"[PERIODIC ANNOUNCEMENT]: {announcement_msg} (after {self.messages_since_last_announcement} messages)")
                        except Exception as e:
                            logger.warning(f"Failed to post periodic announcement: {e}")
                    else:
                        logger.debug(f"[PERIODIC ANNOUNCEMENT SKIPPED]: Only {self.messages_since_last_announcement} messages since last announcement (need {self.min_messages_for_announcement})")
                
                # Fetch new messages using pytchat
                for c in chat.get().sync_items():
                    # Convert pytchat message to our format
                    msg_data = {
                        'id': c.id,
                        'author': c.author.name,
                        'author_channel_id': c.author.channelId,
                        'message': c.message,
                        'timestamp': c.datetime,
                        'is_moderator': c.author.isChatModerator,
                        'is_owner': c.author.isChatOwner,
                        'type': 'text'  # pytchat only provides text messages
                    }
                    await self.process_message(msg_data)
                
                # Track viewer count periodically
                if current_time - self.last_viewer_snapshot >= self.viewer_snapshot_interval:
                    try:
                        stats = self.youtube.get_stream_stats()
                        if stats:
                            self.analytics.track_viewer_count(
                                stats.get('viewer_count', 0),
                                stats.get('likes', 0)
                            )
                            # Update growth features with current subscriber count
                            subscriber_count = stats.get('subs', 0)
                            if subscriber_count > 0:
                                self.growth.update_subscriber_count(subscriber_count)
                            self.last_viewer_snapshot = current_time
                    except Exception as e:
                        logger.error(f"Error tracking viewer count: {e}")
                
                # Wait a bit before checking again
                await asyncio.sleep(1.0)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt - stopping chat bridge...")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Error in chat bridge loop: {e}")
                await asyncio.sleep(5)
        
        # Cancel the intro task
        if 'intro_task' in locals():
            intro_task.cancel()
            try:
                await intro_task
            except asyncio.CancelledError:
                pass
        
        # Note: stats_task removed as part of quota optimization - use !stats command instead
        
        # End analytics session when stopping
        self.analytics.end_session()
        logger.info("Analytics session ended")
        logger.info("Bot shutdown complete")
    
    async def process_message(self, message: dict):
        """
        Process a single chat message or special event (like membership)
        
        Args:
            message: Message dictionary from YouTube API
        """
        # Skip if already processed
        if message['id'] in self.processed_messages:
            logger.debug(f"Skipping already processed message: {message['id']}")
            return
        
        self.processed_messages.add(message['id'])
        self.save_message_id(message['id'])
        
        # ========== HANDLE MEMBERSHIP EVENTS ==========
        # Check if this is a membership/subscription event
        if message.get('type') == 'membership':
            author = message['author']
            logger.info(f"🎉 [NEW MEMBER] {author} just subscribed!")
            
            # Generate thank you message for new subscriber
            thank_you_messages = [
                f"🎉 Welcome to the channel {author}! Thanks for subscribing! - {self.bot_name}",
                f"Thanks for the support {author}! Welcome to the community! 💪 - {self.bot_name}",
                f"Amazing! {author} just joined as a member! Thanks so much! 🙌 - {self.bot_name}",
                f"Huge thanks {author} for the subscription! 🔥 - {self.bot_name}",
            ]
            
            import random
            response = random.choice(thank_you_messages)
            
            # Post thank you message
            await asyncio.sleep(self.response_delay)
            message_id = self.youtube.post_message(response)
            if message_id:
                self.processed_messages.add(message_id)
                self.save_message_id(message_id)
                self.recent_bot_messages.append(self._normalize_text(response))
                logger.info(f"[BOT - THANK YOU]: {response}")
            
            # Track in analytics
            self.analytics.track_message(
                message['id'],
                author,
                message['author_channel_id'],
                f"[MEMBERSHIP] Subscribed",
                False,
                None
            )
            return  # Exit early, no further processing needed
        
        # ========== HANDLE REGULAR TEXT MESSAGES ==========
        # Check if this message matches something the bot recently sent
        # Normalize to avoid mismatches due to formatting/newlines removed by YouTube/pytchat
        incoming_normalized = self._normalize_text(message['message'])
        if incoming_normalized in self.recent_bot_messages:
            logger.info(f"[SELF-MESSAGE FILTER] Skipping: {message['message'][:50]}...")
            return


            logger.info("[SELF-MESSAGE FILTER] Skipping Valorant guidance message")
            return
        
        # Apply filters
        if self.ignore_moderators and message['is_moderator']:
            logger.debug(f"Ignoring moderator message from {message['author']}")
            return
        
        if self.ignore_owner and message['is_owner']:
            logger.debug(f"Ignoring owner message from {message['author']}")
            return
        
        author = message['author']
        text = message['message']
        
        logger.info(f"[{author}]: {text}")
        
        # ========== TRACK GROWTH FEATURES ==========
        # Check if this is a new viewer and generate welcome
        is_new_viewer = self.growth.is_new_viewer(author)
        if is_new_viewer:
            welcome_message = self.growth.get_new_viewer_welcome(author)
            logger.info(f"[NEW VIEWER WELCOME]: {welcome_message}")
            # We'll post this after the main message processing
            # Store it to send after response (if any) to avoid message flooding
        
        # Track message for activity
        self.growth.track_message(author)
        
        # Track message count for periodic announcements
        self.messages_since_last_announcement += 1
        
        # Track message in analytics
        is_command = text.startswith("!")
        command_name = None
        if is_command and " " in text:
            command_name = text.split()[0][1:]  # Remove ! and get command name
        elif is_command:
            command_name = text[1:]  # Just the command without !
        
        self.analytics.track_message(
            message['id'],
            author,
            message['author_channel_id'],
            text,
            is_command,
            command_name
        )
        
        # 1. First, try to get a quick response from a skill
        context = {
            "streamer_profile": self.streamer_profile,
            "current_game": self.current_game,
            "stream_topic": self.stream_topic,
            "youtube_api": self.youtube,
        }

        # Viewer count check disabled for testing

        # 1. Check if message is a command (starts with !)
        response = None
        command_start_time = time.time()
        command_success = False
        
        if text.startswith("!"):
            if self.command_parser.can_handle(text):
                logger.debug(f"Handling command from {author}: {text[:40]}...")
                cmd_context = CommandContext(
                    author=author,
                    message=text,
                    youtube_api=self.youtube,
                    streamer_profile=self.streamer_profile,
                    current_game=self.current_game,
                    stream_topic=self.stream_topic,
                    admin_users=self.admin_users
                )
                try:
                    response = await self.command_parser.execute(text, cmd_context)
                    command_success = True if response else False
                except Exception as e:
                    logger.error(f"Command execution error: {e}")
                    command_success = False
                
                # Track command execution
                if command_name:
                    command_time = time.time() - command_start_time
                    self.analytics.track_command_execution(command_name, command_success, command_time)

        # 2. If not a command, try skills
        if not response and not text.startswith("!"):
            response = await self.skills.dispatch(author, text, context)

        # 3. If no skill handled it, check if the agent should respond
        if not response and not text.startswith("!"):
            should_respond = self.should_respond_to_message(text)
            if should_respond:
                enable_agent = os.getenv("ENABLE_AGENT", "true").strip().lower()
                if enable_agent in ("1", "true", "yes", "y"):
                    logger.debug(f"Agent enabled - generating response for: {text[:50]}...")
                    response = await self.generate_response(author, text)

        # 4. If we have a response from any source, post it
        if response:
            # Add bot signature/username to the response
            response_with_signature = self._append_bot_signature(response)
            
            # Add delay to avoid spam
            await asyncio.sleep(self.response_delay)
            # Post response to YouTube chat
            message_id = self.youtube.post_message(response_with_signature)
            if message_id:
                # Add the bot's own message ID to processed messages so we don't reply to it
                self.processed_messages.add(message_id)
                self.save_message_id(message_id)
                # Add text to recent messages cache (normalized) to avoid self-replies via pytchat
                self.recent_bot_messages.append(self._normalize_text(response_with_signature))
                logger.info(f"[BOT]: {response_with_signature}")
            else:
                logger.warning("Failed to post response")
        
        # 5. POST NEW VIEWER WELCOME (if applicable)
        if is_new_viewer:
            await asyncio.sleep(self.response_delay)
            
            # Check if this is a returning viewer with historical data
            is_returning = self.growth.is_returning_viewer(author)
            
            if is_returning:
                # Use personalized returning viewer message
                welcome_message = self.growth.get_returning_viewer_welcome(author)
                logger.info(f"[RETURNING VIEWER]: {author} - using personalized welcome")
            else:
                # Use generic new viewer message
                welcome_message = self.growth.get_new_viewer_welcome(author)
                logger.info(f"[NEW VIEWER]: {author} - completely new viewer")
            
            welcome_msg_id = self.youtube.post_message(welcome_message)
            if welcome_msg_id:
                self.processed_messages.add(welcome_msg_id)
                self.save_message_id(welcome_msg_id)
                self.recent_bot_messages.append(self._normalize_text(welcome_message))
                logger.info(f"[VIEWER WELCOME]: {welcome_message}")
    
    def should_respond_to_message(self, message: str) -> bool:
        """
        Determine if the bot should respond to a message
        
        PHILOSOPHY: Only respond when the message is directed at the bot (tagged with @StreamNova).
        This avoids interrupting conversations between viewers.
        
        Args:
            message: The message text
            
        Returns:
            True if bot should respond, False otherwise
        """
        import re
        
        msg_lower = message.lower().strip()
        
        # ========== MENTION REQUIREMENT ==========
        # Bot only responds if explicitly mentioned with @StreamNova
        if f'@{self.bot_name.lower()}' not in msg_lower:
            logger.debug(f"Message doesn't mention @{self.bot_name} - ignoring: {message[:30]}...")
            return False
        
        logger.debug(f"Bot mentioned (@{self.bot_name}): {message[:50]}...")
        return True
        
        is_standalone_greeting = any(re.match(pattern, msg_lower) for pattern in greeting_patterns)
        if is_standalone_greeting:
            logger.debug(f"Standalone greeting (not to another user): {message[:30]}...")
            return True
        
        # 4. Direct Questions about the streamer/bot (only questions that clearly need answering)
        # Must start with question word to be "direct"
        if '?' in msg_lower:
            # IMPORTANT: Check if question is about another viewer (e.g., "How are you Rambo?")
            # Pattern: Question word + "you/your" + a person's name (not bot name)
            person_name_pattern = r'^(how|what|why|kaise|kya|kyun)\s+.*\s+(are|is|do)\s+you\s+(\w+)'
            person_match = re.search(person_name_pattern, msg_lower)
            if person_match:
                mentioned_name = person_match.group(4)  # Get the name after "you"
                bot_names_set = {'loki', 'bot', 'host', 'streamer', self.bot_name.lower()}
                # If the name is NOT the bot, it's a viewer-to-viewer question
                if mentioned_name.lower() not in bot_names_set:
                    logger.debug(f"Question to another viewer '{mentioned_name}': {message[:30]}...")
                    return False
            
            # Question word patterns - must be at the very START
            direct_question_patterns = [
                r'^(what|kya|kyaa)\s+.*(you|your|bot|loki|' + self.bot_name.lower() + r'|streak|setup)',
                r'^(why|kyun)\s+.*(you|your|play|stream)',
                r'^(how|kaise)\s+.*(you|your|do|play)',
                r'^(who|kaun)\s+.*(are|ho)',
                r'^(when|kab)\s+.*(you|stream)',
                r'^(what|kya).*(game|valorant|rank|stats)',
            ]
            
            is_direct_question = any(re.search(pattern, msg_lower) for pattern in direct_question_patterns)
            
            if is_direct_question:
                logger.debug(f"Direct question to bot/streamer: {message[:30]}...")
                return True
            else:
                # Question mark present but not directed at bot
                logger.debug(f"Question but not to bot (viewer chat): {message[:30]}...")
                return False
        
        # 5. Explicit Help Requests
        help_keywords = ['help', 'madad', 'sawal', 'puch']
        help_pattern = r'\b(' + '|'.join(help_keywords) + r')\b'
        if re.search(help_pattern, msg_lower):
            logger.debug(f"Explicit help request: {message[:30]}...")
            return True
        
        # 6. Specs/Setup Keywords (only if asking question or mention bot)
        specs_keywords = ['specs', 'pc', 'system', 'gpu', 'cpu', 'ram', 'setup', 'config', 'build']
        specs_pattern = r'\b(' + '|'.join(specs_keywords) + r')\b'
        if re.search(specs_pattern, msg_lower):
            logger.debug(f"Specs mention: {message[:30]}...")
            return True
        
        # ========== DEFAULT: DON'T RESPOND ==========
        # Better to be silent than interrupt viewer conversations
        logger.debug(f"Viewer chat - no response: {message[:30]}...")
        return False
    
    async def generate_response(self, author: str, message: str) -> Optional[str]:
        """
        Generate a response using the ADK agent
        
        Args:
            author: Name of the message author
            message: The message text
            
        Returns:
            Generated response text or None if generation fails
        """
        try:
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.genai import types as genai_types
            
            logger.debug(f"Generating response for {author}: {message[:30]}...")
            
            # Create context-aware prompt
            prompt = f"Viewer '{author}' says: {message}"
            
            # Create session service (stateless for now per request to avoid complexity)
            session_service = InMemorySessionService()
            await session_service.create_session(
                app_name="youtube_chat_bot",
                user_id="youtube_audience",
                session_id="youtube_chat"
            )
            
            # Create runner
            runner = Runner(agent=self.agent, session_service=session_service, app_name="youtube_chat_bot")
            
            # Run agent and collect response
            response_text = ""
            async for event in runner.run_async(
                user_id="youtube_audience",
                session_id="youtube_chat",
                new_message=genai_types.Content(parts=[genai_types.Part(text=prompt)])
            ):
                # Extract text from different event types
                if hasattr(event, 'text') and event.text:
                    response_text += event.text
                elif hasattr(event, 'content'):
                    if isinstance(event.content, str):
                        response_text += event.content
                    elif hasattr(event.content, 'text'):
                        response_text += event.content.text
                    elif hasattr(event.content, 'parts'):
                         for part in event.content.parts:
                             if hasattr(part, 'text') and part.text:
                                 response_text += part.text
            
            # Clean up response text (remove function call artifacts if any)
            if not response_text:
                logger.warning(f"Agent generated no response for message from {author}")
                return None
                
            # Ensure response is not too long for YouTube (max 200 chars is safe)
            if len(response_text) > 200:
                response_text = response_text[:197] + "..."
                
            logger.debug(f"Agent response generated: {response_text[:50]}...")
            return response_text.strip()
                
        except Exception as e:
            # Handle leaked/invalid API key and other LLM failures gracefully
            err_text = str(e)
            
            # Handle Rate Limits (429) specifically to avoid error spam
            if "RESOURCE_EXHAUSTED" in err_text or "429" in err_text:
                logger.warning("Gemini API Rate Limit (429) hit. Skipping response to cool down.")
                return None
            
            # Handle Model Not Found (404)
            if "NOT_FOUND" in err_text or "404" in err_text:
                logger.error(f"Gemini Model Error: {err_text}. Check model name in agent.py.")
                return None

            logger.error(f"Error generating response: {err_text}")
            if "PERMISSION_DENIED" in err_text or "API key" in err_text:
                # Provide a short fallback message so bot doesn't crash mid-stream
                msg_lower = message.lower()
                if "valorant" in msg_lower and any(k in msg_lower for k in ["rank", "kd", "rr"]):
                    return "Stats are temporarily unavailable—will share after the stream."
                return "Got it! I'm here—LLM is momentarily unavailable."
            logger.exception("Traceback:")
            return None
    
    def stop(self):
        """Stop the chat bridge"""
        self.is_running = False
        logger.info("Chat bridge stopped")


# Standalone function for easy usage
async def run_youtube_chat_bot(
    video_id: str,
    agent_name: str = "youtube_chat_advanced",
    streamer_profile: dict = None,
    current_game: str = None,
    stream_topic: str = None,
    bot_name: str = "StreamNova",
    bot_username: str = "StreamNova",
    admin_users: list = None
):
    """
    Run the YouTube chat bot
    
    Args:
        video_id: YouTube video ID
        agent_name: Name of the agent to use (default: youtube_chat_advanced)
        streamer_profile: Dictionary containing streamer details
        current_game: Name of the game being played
        stream_topic: Topic of the stream (if not gaming)
        bot_name: Name of the bot to use in messages (default: StreamNova)
        bot_username: Custom username/signature for bot responses (default: StreamNova)
        admin_users: List of admin usernames who can execute restricted commands
    """
    logger.info(f"Starting YouTube chat bot for video: {video_id}")
    
    # Import the agent
    if agent_name == "youtube_chat_advanced":
        from youtube_chat_advanced.agent import root_agent
    else:
        logger.warning(f"Unknown agent: {agent_name}. Using youtube_chat_advanced by default.")
        from youtube_chat_advanced.agent import root_agent
    
    # Customize agent instructions with profile and game info
    if streamer_profile or current_game or stream_topic:
        context_instruction = "\n\nStream Context & Personalization:\n"
        if current_game:
            context_instruction += f"Current Game: You are currently moderating a stream of the game '{current_game}'. Use your knowledge of this game to answer questions and engage with viewers.\n"
        elif stream_topic:
            context_instruction += f"Stream Topic: You are currently moderating a stream about '{stream_topic}'. Use your knowledge of this topic to engage with viewers.\n"
            
        if streamer_profile:
            context_instruction += "YOUR PERSONAL PROFILE (You are the streamer):\n"
            for key, value in streamer_profile.items():
                context_instruction += f"- {key}: {value}\n"
            
            context_instruction += "\nIMPORTANT INSTRUCTION ON IDENTITY:\n"
            context_instruction += "You are NOT an assistant. You ARE the streamer listed in the profile above.\n"
            context_instruction += "When answering questions like 'what is your name?' or 'what do you do?', use the profile information as YOUR own.\n"
            context_instruction += "Speak in the first person ('I am...', 'My name is...').\n"
            context_instruction += "Example: If asked 'what do you do?', answer 'I am an IT Professional'.\n"
            
            streamer_name = streamer_profile.get('Name', 'the streamer')
            context_instruction += f"\nGeneral Knowledge: Answer common general knowledge questions (e.g., capitals, dates, facts) directly and briefly.\n"
            context_instruction += f"FALLBACK: If you cannot answer a stream-specific or technical question, reply with: 'I will let {streamer_name} answer this question.'\n"
        
        # Append to existing instructions
        root_agent.instruction += context_instruction
        logger.info("Agent instructions updated with stream context.")

    # Create and start bridge
    bridge = YouTubeChatBridge(
        video_id=video_id,
        agent=root_agent,
        streamer_profile=streamer_profile,
        current_game=current_game,
        stream_topic=stream_topic,
        response_delay=2.0,
        bot_name=bot_name,
        bot_username=bot_username,
        admin_users=admin_users or []
    )
    
    # Initialize subscriber count from YouTube
    bridge._initialize_subscriber_count()
    
    await bridge.start()
