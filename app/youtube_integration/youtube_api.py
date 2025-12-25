"""
YouTube Live Chat API Integration Module
Handles fetching messages from YouTube live streams and posting responses
"""

import os
import time
import logging
import pickle
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
try:
    try:
        # Works when running from local workspace where code is under `app/`
        from app.logger import get_logger
    except ModuleNotFoundError:
        # Fallback for GitHub Actions / repo root where modules are at top-level
        from logger import get_logger
except ImportError:
    from logger import get_logger
try:
    from app.logger import get_logger
except ImportError:
    from logger import get_logger

# Scopes required for reading and posting to live chat
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

logger = get_logger(__name__)

class YouTubeLiveChatAPI:
    """Handles YouTube Live Chat API interactions"""
    
    def __init__(self, client_secrets_file: str = "client_secret.json"):
        """
        Initialize YouTube API client with OAuth 2.0
        
        Args:
            client_secrets_file: Path to the client_secret.json file
        """
        # If relative path, make it absolute based on app directory
        if not os.path.isabs(client_secrets_file):
            # Get the app directory (parent of youtube_integration)
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.client_secrets_file = os.path.join(app_dir, client_secrets_file)
        else:
            self.client_secrets_file = client_secrets_file
            
        self.credentials = None
        self.youtube = None
        self.live_chat_id = None
        self.next_page_token = None
        self.processed_message_ids = set()
        self.my_channel_id = None
        
        # Cache for stream stats to reduce API calls
        self.stats_cache = None
        self.stats_cache_time = 0
        self.stats_cache_ttl = 300  # Cache for 5 minutes
        
    def authenticate(self):
        """Performs OAuth 2.0 authentication"""
        creds = None
        # Store token in app directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        token_file = os.path.join(app_dir, 'token.pickle')
        
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
                logger.debug("Loaded credentials from token.pickle")
                
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired credentials...")
                    creds.refresh(Request())
                    logger.info("Credentials refreshed successfully")
                except Exception as e:
                    logger.error(f"Error refreshing token: {e}")
                    os.remove(token_file)
                    return self.authenticate()
            else:
                if not os.path.exists(self.client_secrets_file):
                    logger.error(f"Client secrets file not found: {self.client_secrets_file}")
                    raise FileNotFoundError(f"Client secrets file not found: {self.client_secrets_file}")
                
                logger.info("Initiating OAuth 2.0 authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("OAuth authentication completed")
                
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            logger.debug("Credentials saved to token.pickle")

        self.credentials = creds
        self.youtube = build('youtube', 'v3', credentials=creds)
        logger.info("Successfully authenticated with YouTube API")
        
        # Get own channel ID
        self.get_my_channel_id()

    def get_my_channel_id(self) -> Optional[str]:
        """
        Get the authenticated user's channel ID
        
        Returns:
            Channel ID if successful, None otherwise
        """
        try:
            request = self.youtube.channels().list(
                part="id",
                mine=True
            )
            response = request.execute()
            
            if response.get('items'):
                self.my_channel_id = response['items'][0]['id']
                logger.info(f"Authenticated as channel: {self.my_channel_id}")
                return self.my_channel_id
            return None
        except HttpError as e:
            logger.error(f"Error getting my channel ID: {e}")
            return None

    def get_live_broadcast_id(self, channel_id: str = None) -> Optional[str]:
        """
        Get the currently active live broadcast ID
        
        Args:
            channel_id: YouTube channel ID (optional, uses authenticated channel if not provided)
            
        Returns:
            Broadcast ID if live stream is active, None otherwise
        """
        try:
            request = self.youtube.liveBroadcasts().list(
                part="id,snippet",
                broadcastStatus="active",
                maxResults=1
            )
            
            response = request.execute()
            
            if response.get('items'):
                broadcast_id = response['items'][0]['id']
                logger.info(f"Found active broadcast: {broadcast_id}")
                return broadcast_id
            else:
                logger.warning("No active live broadcast found")
                return None
                
        except HttpError as e:
            logger.error(f"Error getting live broadcast: {e}")
            return None
    
    def get_current_live_video_id(self) -> Optional[str]:
        """
        Get the video ID of the currently active live stream for the authenticated channel
        
        Returns:
            Video ID if a live stream is active, None otherwise
        """
        try:
            # Get active broadcasts
            request = self.youtube.liveBroadcasts().list(
                part="id,snippet,contentDetails",
                broadcastStatus="active",
                maxResults=1
            )
            
            response = request.execute()
            
            if response.get('items'):
                broadcast = response['items'][0]
                # Get the bound stream's video ID
                video_id = broadcast['id']
                title = broadcast['snippet'].get('title', 'Unknown')
                logger.info(f"Found active live stream: '{title}' (Video ID: {video_id})")
                return video_id
            else:
                logger.warning("No active live stream found on your channel")
                logger.info("Make sure you have started a live stream before running the bot")
                return None
                
        except HttpError as e:
            logger.error(f"Error getting current live video: {e}")
            return None
    
    def get_live_chat_id(self, video_id: str) -> Optional[str]:
        """
        Get the live chat ID for a video
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Live chat ID if available, None otherwise
        """
        try:
            request = self.youtube.videos().list(
                part="liveStreamingDetails",
                id=video_id
            )
            
            response = request.execute()
            
            if response.get('items'):
                live_details = response['items'][0].get('liveStreamingDetails', {})
                chat_id = live_details.get('activeLiveChatId')
                
                if chat_id:
                    self.live_chat_id = chat_id
                    logger.info(f"Live chat ID: {chat_id}")
                    return chat_id
                else:
                    logger.warning("No active live chat found for this video")
                    return None
            else:
                logger.warning("Video not found")
                return None
                
        except HttpError as e:
            logger.error(f"Error getting live chat ID: {e}")
            return None
    
    def fetch_chat_messages(self) -> List[Dict]:
        """
        Fetch new messages from the live chat
        
        Returns:
            List of message dictionaries with 'author', 'message', and 'id'
        """
        if not self.live_chat_id:
            logger.warning("No live chat ID set. Call get_live_chat_id first.")
            return []
        
        try:
            request = self.youtube.liveChatMessages().list(
                liveChatId=self.live_chat_id,
                part="snippet,authorDetails",
                maxResults=200,
                pageToken=self.next_page_token
            )
            
            response = request.execute()
            
            # Update page token for next fetch
            self.next_page_token = response.get('nextPageToken')
            
            # Extract messages
            messages = []
            for item in response.get('items', []):
                message_id = item['id']
                
                # Skip already processed messages
                if message_id in self.processed_message_ids:
                    continue
                
                self.processed_message_ids.add(message_id)
                
                snippet = item['snippet']
                author_details = item['authorDetails']
                
                # Only process text messages (ignore superchats, member messages for now)
                if snippet.get('type') == 'textMessageEvent':
                    messages.append({
                        'id': message_id,
                        'author': author_details['displayName'],
                        'author_channel_id': author_details['channelId'],
                        'message': snippet['displayMessage'],
                        'timestamp': snippet['publishedAt'],
                        'is_moderator': author_details.get('isChatModerator', False),
                        'is_owner': author_details.get('isChatOwner', False)
                    })
            
            # Get polling interval from response
            # Enforce a minimum of 10 seconds to save quota (extends runtime to ~5-6 hours)
            api_interval = response.get('pollingIntervalMillis', 10000) / 1000.0
            polling_interval = max(api_interval, 10.0)
            logger.debug(f"Fetched {len(messages)} new messages, polling interval: {polling_interval}s")
            
            return messages, polling_interval
            
        except HttpError as e:
            # Check for quota exceeded error
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                logger.critical("YOUTUBE API QUOTA EXCEEDED - Cannot continue fetching messages")
                # Return a very long sleep time to stop the loop effectively
                return [], 3600.0
                
            logger.error(f"Error fetching chat messages: {e}")
            return [], 10.0
    
    def post_message(self, message: str) -> Optional[str]:
        """
        Post a message to the live chat
        
        Args:
            message: The message text to post
            
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.live_chat_id:
            logger.warning("No live chat ID set. Call get_live_chat_id first.")
            return None
        
        try:
            # Safety: truncate long messages to avoid INVALID_REQUEST_METADATA
            if message and len(message) > 200:
                message = message[:197] + "..."
            request = self.youtube.liveChatMessages().insert(
                part="snippet",
                body={
                    "snippet": {
                        "liveChatId": self.live_chat_id,
                        "type": "textMessageEvent",
                        "textMessageDetails": {
                            "messageText": message
                        }
                    }
                }
            )
            
            response = request.execute()
            logger.debug(f"Message posted: {message[:50]}...")
            return response.get('id')
            
        except HttpError as e:
            # Handle quota exceeded error gracefully
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                logger.error("YOUTUBE API QUOTA EXCEEDED - Cannot post messages. Bot will continue reading messages via pytchat.")
                return None
            logger.error(f"Error posting message: {e}")
            return None
    
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message from the live chat (requires moderator permissions)
        
        Args:
            message_id: The ID of the message to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            request = self.youtube.liveChatMessages().delete(
                id=message_id
            )
            
            request.execute()
            logger.info(f"Message deleted: {message_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Error deleting message: {e}")
            return False
    
    def is_stream_active(self, video_id: str) -> bool:
        """
        Check if a stream is currently active/live
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if stream is live, False otherwise
        """
        try:
            request = self.youtube.videos().list(
                part="snippet,liveStreamingDetails",
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                return False
                
            item = response['items'][0]
            live_details = item.get('liveStreamingDetails', {})
            
            # Check if stream has an active live chat and is actually live
            has_active_chat = live_details.get('activeLiveChatId') is not None
            actual_end_time = live_details.get('actualEndTime')
            
            # Stream is active if it has active chat and hasn't ended
            is_active = has_active_chat and actual_end_time is None
            
            if not is_active:
                logger.info(f"Stream {video_id} is no longer active")
            
            return is_active
            
        except Exception as e:
            logger.error(f"Error checking stream status: {e}")
            # Return True on error to avoid premature shutdown
            return True
    
    def get_stream_stats(self, video_id: str = None, use_cache: bool = True) -> Optional[Dict[str, int]]:
        """
        Get current stream stats: viewer count, likes, and subs
        Args:
            video_id: YouTube video ID (optional, uses current broadcast if not provided)
            use_cache: If True, return cached stats if available (default: True, saves quota)
        Returns:
            Dict with 'viewer_count', 'likes', 'subs' or None if error
        """
        # Check cache first to save API quota
        if use_cache and self.stats_cache is not None:
            cache_age = time.time() - self.stats_cache_time
            if cache_age < self.stats_cache_ttl:
                logger.debug(f"Returning cached stats (age: {cache_age:.0f}s)")
                return self.stats_cache
        
        try:
            # If no video_id provided, get current broadcast
            if video_id is None:
                broadcast_id = self.get_live_broadcast_id()
                if not broadcast_id:
                    return None
                video_id = broadcast_id
            request = self.youtube.videos().list(
                part="liveStreamingDetails,statistics",
                id=video_id
            )
            response = request.execute()
            if not response.get('items'):
                return None
            item = response['items'][0]
            live_details = item.get('liveStreamingDetails', {})
            stats = item.get('statistics', {})
            viewer_count = int(live_details.get('concurrentViewers', 0))
            likes = int(stats.get('likeCount', 0))
            subs = None
            # Get subs from channel statistics
            if self.my_channel_id:
                channel_req = self.youtube.channels().list(
                    part="statistics",
                    id=self.my_channel_id
                )
                channel_resp = channel_req.execute()
                if channel_resp.get('items'):
                    subs = int(channel_resp['items'][0]['statistics'].get('subscriberCount', 0))
            logger.debug(f"Stream stats - Viewers: {viewer_count}, Likes: {likes}, Subs: {subs}")
            
            # Update cache
            result = {
                'viewer_count': viewer_count,
                'likes': likes,
                'subs': subs if subs is not None else 0
            }
            self.stats_cache = result
            self.stats_cache_time = time.time()
            
            return result
        except Exception as e:
            logger.error(f"Error getting stream stats: {e}")
            return None

    def ban_user(self, channel_id: str, ban_duration_seconds: int = None) -> bool:
        """
        Ban a user from the live chat
        
        Args:
            channel_id: The channel ID of the user to ban
            ban_duration_seconds: Duration in seconds (None for permanent ban)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ban_details = {
                "liveChatId": self.live_chat_id,
                "type": "permanent" if ban_duration_seconds is None else "temporary",
                "bannedUserDetails": {
                    "channelId": channel_id
                }
            }
            
            if ban_duration_seconds is not None:
                ban_details["banDurationSeconds"] = ban_duration_seconds
            
            request = self.youtube.liveChatBans().insert(
                part="snippet",
                body={"snippet": ban_details}
            )
            
            response = request.execute()
            logger.info(f"User banned: {channel_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Error banning user: {e}")
            return False
