from typing import Optional, Dict, Any
from .skills import BaseSkill


class FunnyHypeSkill(BaseSkill):
    name = "funny_hype"
    description = "Drops short hype lines and light jokes triggered by events."

    def should_handle(self, author: str, message: str) -> bool:
        triggers = ["gg", "clutch", "win", "pog", "let's go", "fire", "insane"]
        stats_triggers = ["stats", "stream stats", "show stats", "!stats"]
        msg_lower = message.lower().strip()
        # Hype triggers
        for t in triggers:
            if msg_lower == t or msg_lower.startswith(f"!{t}"):
                return True
        # Stats triggers
        for s in stats_triggers:
            if msg_lower == s or msg_lower.startswith(f"!{s}"):
                return True
        return False

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        stats_triggers = ["stats", "stream stats", "show stats", "!stats"]
        msg_lower = message.lower().strip()
        # Stats request
        for s in stats_triggers:
            if msg_lower == s or msg_lower.startswith(f"!{s}"):
                # Expect context to have 'youtube_api' instance
                youtube_api = context.get("youtube_api")
                if youtube_api:
                    stats = youtube_api.get_stream_stats()
                    if stats:
                        return f"📊 Stream Stats: {stats['viewer_count']} watching, {stats['likes']} likes, {stats['subs']} subs!"
                    else:
                        return "Could not fetch stream stats right now."
                else:
                    return "YouTube API not available for stats."
        # Hype lines
        lines = [
            "That was clean! 🚀",
            "Chat, spam GG—this is heat! 🔥",
            "Certified clutch moment. 🏆",
            "Okay that was kinda cracked ngl 💯",
        ]
        idx = (hash(message) % len(lines))
        return lines[idx]