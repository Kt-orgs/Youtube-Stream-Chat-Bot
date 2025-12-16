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
    from app.constants import GREETING_WORDS, HYPE_TRIGGERS, SPECS_KEYWORDS, HELP_KEYWORDS, QUESTION_MARKERS
    from app.logger import get_logger
    from app.commands import (
        CommandParser, CommandContext,
        HelpCommand, PingCommand, UptimeCommand, SocialsCommand, StatusCommand,
        ValorantStatsCommand, ValorantAgentCommand, ValorantMapCommand,
        ViewersCommand, LeaderboardCommand, BotStatsCommand, ExportCommand
    )
    from app.analytics import get_analytics_tracker
except ImportError:
    from skills import SkillRegistry, GreetingSkill, CommunityEngagementSkill, AICoHostSkill, FunnyHypeSkill, SmartGamingAssistantSkill, GrowthBoosterSkill
    from constants import GREETING_WORDS, HYPE_TRIGGERS, SPECS_KEYWORDS, HELP_KEYWORDS, QUESTION_MARKERS
    from logger import get_logger
    from commands import (
        CommandParser, CommandContext,
        HelpCommand, PingCommand, UptimeCommand, SocialsCommand, StatusCommand,
        ValorantStatsCommand, ValorantAgentCommand, ValorantMapCommand,
        ViewersCommand, LeaderboardCommand, BotStatsCommand, ExportCommand
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
        ignore_owner: bool = False
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
        self.command_parser.register(BotStatsCommand())
        self.command_parser.register(ExportCommand())
        logger.debug(f"Registered {len(self.command_parser.get_all_commands())} commands")
        
        # Persistence for processed messages
        self.history_file = "processed_messages.txt"
        self.processed_messages = self.load_history()
        
        # Cache to store recent bot messages to avoid self-replies
        self.recent_bot_messages = deque(maxlen=20)
        
        # Analytics tracker
        self.analytics = get_analytics_tracker()
        self.viewer_snapshot_interval = 60  # Track viewers every 60 seconds
        self.last_viewer_snapshot = 0
        
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
            
        # Initialize pytchat for reading messages (No quota usage)
        try:
            # In GitHub Actions, we might be testing with a video ID that pytchat can't access
            # or the environment might be restricted. We'll add a fallback or skip if it fails.
            chat = pytchat.create(video_id=self.video_id)
            logger.info("Pytchat initialized successfully (Quota-free reading mode)")
        except Exception as e:
            logger.error(f"Error initializing pytchat: {e}")
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                logger.warning("Running in GitHub Actions - skipping pytchat initialization failure to allow bot to continue (testing mode)")
                # Create a dummy chat object for testing
                class DummyChat:
                    def is_alive(self): return True
                    def get(self): 
                        class DummyItems:
                            def sync_items(self): return []
                        return DummyItems()
                chat = DummyChat()
            else:
                return
        
        self.is_running = True
        logger.info("Chat bridge started successfully!")
        logger.info("Monitoring chat for messages...")
        
        # Start analytics session
        stream_title = self.stream_topic or self.current_game or "Unknown"
        game = self.current_game or ""
        self.analytics.start_session(self.video_id, stream_title, game)
        logger.info("Analytics session started")
        
        # Start periodic stats poster
        async def post_stats_periodically():
            while self.is_running:
                try:
                    stats = self.youtube.get_stream_stats()
                    if stats:
                        msg = (
                            f"📊 Stream Stats: {stats['viewer_count']} watching, {stats['likes']} likes, {stats['subs']} subs! "
                            f"If you're enjoying the stream, don't forget to like 👍 and subscribe ❤️ for more content!"
                        )
                        # Add to cache BEFORE posting to prevent race condition
                        self.recent_bot_messages.append(msg)
                        
                        message_id = self.youtube.post_message(msg)
                        if message_id:
                            # Pre-emptively add to processed messages before it appears in chat
                            self.processed_messages.add(message_id)
                            self.save_message_id(message_id)
                            logger.info(f"[Periodic Stats] Posted (ID: {message_id}): {msg[:80]}...")
                        else:
                            logger.warning("Failed to post periodic stats message")
                    else:
                        logger.warning("Could not fetch stream stats for periodic post.")
                except Exception as e:
                    logger.error(f"Error in periodic stats poster: {e}")
                await asyncio.sleep(900)  # 15 minutes

        # Start the periodic stats poster as a background task
        stats_task = asyncio.create_task(post_stats_periodically())

        # Main loop
        while self.is_running and chat.is_alive():
            try:
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
                        'is_owner': c.author.isChatOwner
                    }
                    await self.process_message(msg_data)
                
                # Track viewer count periodically
                current_time = time.time()
                if current_time - self.last_viewer_snapshot >= self.viewer_snapshot_interval:
                    try:
                        stats = self.youtube.get_stream_stats()
                        if stats:
                            self.analytics.track_viewer_count(
                                stats.get('viewer_count', 0),
                                stats.get('likes', 0)
                            )
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
        
        # End analytics session when stopping
        self.analytics.end_session()
        logger.info("Analytics session ended")
    
    async def process_message(self, message: dict):
        """
        Process a single chat message
        
        Args:
            message: Message dictionary from YouTube API
        """
        # Skip if already processed
        if message['id'] in self.processed_messages:
            logger.debug(f"Skipping already processed message: {message['id']}")
            return
        
        self.processed_messages.add(message['id'])
        self.save_message_id(message['id'])
        
        # Check if this message matches something the bot recently sent
        # This prevents the bot from replying to itself when running on the streamer's account
        if message['message'] in self.recent_bot_messages:
            logger.info(f"[SELF-MESSAGE FILTER] Skipping: {message['message'][:50]}...")
            return
        
        # Also skip periodic stats messages by pattern
        if message['message'].startswith("📊 Stream Stats:"):
            logger.info("[STATS FILTER] Skipping periodic stats message")
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
                    stream_topic=self.stream_topic
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
            # Add delay to avoid spam
            await asyncio.sleep(self.response_delay)
            # Post response to YouTube chat
            message_id = self.youtube.post_message(response)
            if message_id:
                # Add the bot's own message ID to processed messages so we don't reply to it
                self.processed_messages.add(message_id)
                self.save_message_id(message_id)
                # Add text to recent messages cache to avoid self-replies via pytchat
                self.recent_bot_messages.append(response)
                logger.info(f"[BOT]: {response}")
            else:
                logger.warning("Failed to post response")
    
    def should_respond_to_message(self, message: str) -> bool:
        """
        Determine if the bot should respond to a message
        
        Args:
            message: The message text
            
        Returns:
            True if bot should respond, False otherwise
        """
        # Customize this logic based on your needs
        
        # Always respond to questions
        question_markers = ['?', 'kya', 'kaise', 'kab', 'kahan', 'kyun', 'what', 'why', 'how', 'who', 'when', 'where']
        if any(marker in message.lower() for marker in question_markers):
            logger.debug(f"Message is a question: {message[:30]}...")
            return True
            
        # Respond to keywords about specs/setup
        specs_keywords = ['specs', 'pc', 'system', 'gpu', 'cpu', 'ram', 'setup', 'config']
        if any(keyword in message.lower() for keyword in specs_keywords):
            logger.debug(f"Message mentions specs: {message[:30]}...")
            return True
        
        # Respond to greetings (but not if it's a command)
        if not message.strip().startswith('!'):
            greetings = ['hi', 'hello', 'hey', 'namaste', 'namaskar', 'hii', 'hlo']
            if any(greeting in message.lower() for greeting in greetings):
                logger.debug(f"Message is a greeting: {message[:30]}...")
                return True
        
        # Respond to help requests
        help_keywords = ['help', 'madad', 'question', 'sawal', 'puch']
        if any(keyword in message.lower() for keyword in help_keywords):
            logger.debug(f"Message is a help request: {message[:30]}...")
            return True
        
        # Don't respond to very short messages (likely reactions)
        if len(message) < 4:
            logger.debug(f"Message too short, ignoring: {message}")
            return False
        
        # You can add more logic here:
        # - Respond only when mentioned by name
        # - Use sentiment analysis
        # - Use keyword filters
        # - Respond to specific command patterns
        
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
    stream_topic: str = None
):
    """
    Run the YouTube chat bot
    
    Args:
        video_id: YouTube video ID
        agent_name: Name of the agent to use (default: youtube_chat_advanced)
        streamer_profile: Dictionary containing streamer details
        current_game: Name of the game being played
        stream_topic: Topic of the stream (if not gaming)
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
        response_delay=2.0
    )
    
    await bridge.start()
