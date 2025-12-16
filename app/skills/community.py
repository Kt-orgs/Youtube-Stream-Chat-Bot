import time
from typing import Optional, Dict, Any
from .skills import BaseSkill

class CommunityEngagementSkill(BaseSkill):
    name = "community_engagement"
    description = "Joins positive chat discussions with friendly comments, but avoids spamming."

    def __init__(self, config=None):
        super().__init__(config)
        self._last_sent: float = 0

    def should_handle(self, author: str, message: str) -> bool:
        msg = message.lower().strip()
        # Trigger on general positive sentiment, not questions or commands
        triggers = ["love", "awesome", "great", "nice", "cool", "vibe", "fun", "enjoy", "favorite", "best", "amazing", "good map", "good game", "gg"]
        # Only trigger if not a question and not a command
        if "?" in msg or msg.startswith("!"):
            return False
        return any(t in msg for t in triggers)

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        now = time.time()
        min_gap = int(self.config.get("min_gap_seconds", 120))
        if now - self._last_sent < min_gap:
            return None
        # Check viewer count from context (if available)
        viewer_count = None
        youtube_api = context.get("youtube_api")
        if youtube_api:
            stats = youtube_api.get_stream_stats()
            if stats:
                viewer_count = stats.get("viewer_count", None)
        if viewer_count is not None and viewer_count <= 0:
            return None
        self._last_sent = now
        streamer = context.get("streamer_profile", {}).get("Name", "the stream")
        comments = [
            f"Love the energy in chat! You all make {streamer}'s stream awesome.",
            "Chat is vibing—keep the good times rolling!",
            "Great to see everyone enjoying the game together.",
            "This community is the best—thanks for hanging out!",
            "So many positive vibes here!",
            "Favorite map discussions always get the chat going!",
            "Glad to see everyone having fun!",
        ]
        import random
        return random.choice(comments)