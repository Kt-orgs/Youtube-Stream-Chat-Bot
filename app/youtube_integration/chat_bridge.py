"""
YouTube Chat Bridge
Connects YouTube Live Chat to Google ADK Agent
"""

import asyncio
import time
import os
from collections import deque
from typing import Optional
import pytchat
from google.adk.agents import Agent
from google.adk import events
from .youtube_api import YouTubeLiveChatAPI


class YouTubeChatBridge:
    """Bridge between YouTube Live Chat and ADK Agent"""
    
    def __init__(
        self,
        youtube_api_key: str,
        agent: Agent,
        video_id: str,
        response_delay: float = 2.0,
        ignore_moderators: bool = False,
        ignore_owner: bool = False
    ):
        """
        Initialize the chat bridge
        
        Args:
            youtube_api_key: Unused, kept for signature compatibility
            agent: The ADK Agent instance to use for generating responses
            video_id: YouTube video ID of the live stream
            response_delay: Delay in seconds before responding (to avoid spam)
            ignore_moderators: If True, don't respond to moderator messages
            ignore_owner: If True, don't respond to channel owner messages
        """
        # Initialize API with OAuth support (for posting only)
        self.youtube = YouTubeLiveChatAPI()
        self.youtube.authenticate()
        
        self.agent = agent
        self.video_id = video_id
        self.response_delay = response_delay
        self.ignore_moderators = ignore_moderators
        self.ignore_owner = ignore_owner
        self.is_running = False
        
        # Persistence for processed messages
        self.history_file = "processed_messages.txt"
        self.processed_messages = self.load_history()
        
        # Cache to store recent bot messages to avoid self-replies
        self.recent_bot_messages = deque(maxlen=20)
        
    def load_history(self) -> set:
        """Load processed message IDs from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return set(line.strip() for line in f if line.strip())
            except Exception as e:
                print(f"Error loading history: {e}")
        return set()

    def save_message_id(self, message_id: str):
        """Save a processed message ID to file"""
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(f"{message_id}\n")
        except Exception as e:
            print(f"Error saving history: {e}")
        
    async def start(self):
        """Start the chat bridge"""
        print(f"Starting YouTube Chat Bridge for video: {self.video_id}")
        
        # Get live chat ID (still needed for posting messages)
        chat_id = self.youtube.get_live_chat_id(self.video_id)
        
        if not chat_id:
            print("Failed to get live chat ID. Make sure the video is live and has chat enabled.")
            return
        
        # Explicitly set the live_chat_id in the API object
        self.youtube.live_chat_id = chat_id
            
        # Initialize pytchat for reading messages (No quota usage)
        try:
            chat = pytchat.create(video_id=self.video_id)
            print("Pytchat initialized successfully (Quota-free reading mode)")
        except Exception as e:
            print(f"Error initializing pytchat: {e}")
            return
        
        self.is_running = True
        print("Chat bridge started successfully!")
        print("Monitoring chat for messages...")
        
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
                
                # Wait a bit before checking again
                await asyncio.sleep(1.0)
                
            except KeyboardInterrupt:
                print("\nStopping chat bridge...")
                self.is_running = False
                break
            except Exception as e:
                print(f"Error in chat bridge loop: {e}")
                await asyncio.sleep(5)
    
    async def process_message(self, message: dict):
        """
        Process a single chat message
        
        Args:
            message: Message dictionary from YouTube API
        """
        # Skip if already processed
        if message['id'] in self.processed_messages:
            return
        
        self.processed_messages.add(message['id'])
        self.save_message_id(message['id'])
        
        # Check if this message matches something the bot recently sent
        # This prevents the bot from replying to itself when running on the streamer's account
        if message['message'] in self.recent_bot_messages:
            print(f"Skipping self-message: {message['message'][:30]}...")
            return
        
        # Apply filters
        if self.ignore_moderators and message['is_moderator']:
            return
        
        if self.ignore_owner and message['is_owner']:
            return
        
        author = message['author']
        text = message['message']
        
        print(f"\n[{author}]: {text}")
        
        # Check if message seems like a question or needs response
        # You can customize this logic
        should_respond = self.should_respond_to_message(text)
        
        if should_respond:
            # Add delay to avoid spam
            await asyncio.sleep(self.response_delay)
            
            # Generate response using ADK agent
            response = await self.generate_response(author, text)
            
            if response:
                # Post response to YouTube chat
                message_id = self.youtube.post_message(response)
                
                if message_id:
                    # Add the bot's own message ID to processed messages so we don't reply to it
                    self.processed_messages.add(message_id)
                    self.save_message_id(message_id)
                    
                    # Add text to recent messages cache to avoid self-replies via pytchat
                    self.recent_bot_messages.append(response)
                    
                    print(f"[BOT]: {response}")
                else:
                    print("Failed to post response")
    
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
            return True
            
        # Respond to keywords about specs/setup
        specs_keywords = ['specs', 'pc', 'system', 'gpu', 'cpu', 'ram', 'setup', 'config']
        if any(keyword in message.lower() for keyword in specs_keywords):
            return True
        
        # Respond to greetings
        greetings = ['hi', 'hello', 'hey', 'namaste', 'namaskar', 'hii', 'hlo']
        if any(greeting in message.lower() for greeting in greetings):
            return True
        
        # Respond to help requests
        help_keywords = ['help', 'madad', 'question', 'sawal', 'puch']
        if any(keyword in message.lower() for keyword in help_keywords):
            return True
        
        # Don't respond to very short messages (likely reactions)
        if len(message) < 4:
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
                return None
                
            # Ensure response is not too long for YouTube (max 200 chars is safe)
            if len(response_text) > 200:
                response_text = response_text[:197] + "..."
                
            return response_text.strip()
                
        except Exception as e:
            print(f"Error generating response: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def stop(self):
        """Stop the chat bridge"""
        self.is_running = False
        print("Chat bridge stopped")


# Standalone function for easy usage
async def run_youtube_chat_bot(
    youtube_api_key: str,
    video_id: str,
    agent_name: str = "youtube_chat_advanced",
    streamer_profile: dict = None,
    current_game: str = None,
    stream_topic: str = None
):
    """
    Run the YouTube chat bot
    
    Args:
        youtube_api_key: YouTube Data API key
        video_id: YouTube video ID
        agent_name: Name of the agent to use (default: youtube_chat_advanced)
        streamer_profile: Dictionary containing streamer details
        current_game: Name of the game being played
        stream_topic: Topic of the stream (if not gaming)
    """
    # Import the agent
    if agent_name == "youtube_chat_advanced":
        from youtube_chat_advanced.agent import root_agent
    else:
        print(f"Unknown agent: {agent_name}. Using youtube_chat_advanced by default.")
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
            context_instruction += f"FALLBACK: If you cannot answer a question based on the profile or general knowledge, reply with: 'I will let {streamer_name} answer this question.'\n"
        
        # Append to existing instructions
        root_agent.instruction += context_instruction
        print("Agent instructions updated with stream context.")

    # Create and start bridge
    bridge = YouTubeChatBridge(
        youtube_api_key=youtube_api_key,
        agent=root_agent,
        video_id=video_id,
        response_delay=2.0
    )
    
    await bridge.start()
