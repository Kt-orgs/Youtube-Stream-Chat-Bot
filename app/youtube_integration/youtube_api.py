"""
YouTube Live Chat API Integration Module
Handles fetching messages from YouTube live streams and posting responses
"""

import os
import time
import pickle
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes required for reading and posting to live chat
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

class YouTubeLiveChatAPI:
    """Handles YouTube Live Chat API interactions"""
    
    def __init__(self, client_secrets_file: str = "client_secret.json"):
        """
        Initialize YouTube API client with OAuth 2.0
        
        Args:
            client_secrets_file: Path to the client_secret.json file
        """
        self.client_secrets_file = client_secrets_file
        self.credentials = None
        self.youtube = None
        self.live_chat_id = None
        self.next_page_token = None
        self.processed_message_ids = set()
        self.my_channel_id = None
        
    def authenticate(self):
        """Performs OAuth 2.0 authentication"""
        creds = None
        token_file = 'token.pickle'
        
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
                
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    os.remove(token_file)
                    return self.authenticate()
            else:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(f"Client secrets file not found: {self.client_secrets_file}")
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        self.credentials = creds
        self.youtube = build('youtube', 'v3', credentials=creds)
        print("Successfully authenticated with YouTube!")
        
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
                print(f"Authenticated as channel: {self.my_channel_id}")
                return self.my_channel_id
            return None
        except HttpError as e:
            print(f"Error getting my channel ID: {e}")
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
                print(f"Found active broadcast: {broadcast_id}")
                return broadcast_id
            else:
                print("No active live broadcast found")
                return None
                
        except HttpError as e:
            print(f"Error getting live broadcast: {e}")
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
                    print(f"Live chat ID: {chat_id}")
                    return chat_id
                else:
                    print("No active live chat found for this video")
                    return None
            else:
                print("Video not found")
                return None
                
        except HttpError as e:
            print(f"Error getting live chat ID: {e}")
            return None
    
    def fetch_chat_messages(self) -> List[Dict]:
        """
        Fetch new messages from the live chat
        
        Returns:
            List of message dictionaries with 'author', 'message', and 'id'
        """
        if not self.live_chat_id:
            print("No live chat ID set. Call get_live_chat_id first.")
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
            
            return messages, polling_interval
            
        except HttpError as e:
            # Check for quota exceeded error
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                print("\n" + "!"*60)
                print("CRITICAL ERROR: YOUTUBE API QUOTA EXCEEDED")
                print("You have used your daily allowance of 10,000 units.")
                print("The bot cannot continue fetching messages until the quota resets.")
                print("(Quota resets at midnight Pacific Time)")
                print("!"*60 + "\n")
                # Return a very long sleep time to stop the loop effectively
                return [], 3600.0
                
            print(f"Error fetching chat messages: {e}")
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
            print("No live chat ID set. Call get_live_chat_id first.")
            return None
        
        try:
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
            print(f"Message posted: {message}")
            return response.get('id')
            
        except HttpError as e:
            print(f"Error posting message: {e}")
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
            print(f"Message deleted: {message_id}")
            return True
            
        except HttpError as e:
            print(f"Error deleting message: {e}")
            return False
    
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
            print(f"User banned: {channel_id}")
            return True
            
        except HttpError as e:
            print(f"Error banning user: {e}")
            return False
