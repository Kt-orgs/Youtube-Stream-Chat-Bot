from typing import Optional, Dict, Any
from .skills import BaseSkill


class AICoHostSkill(BaseSkill):
    name = "ai_cohost"
    description = "Conversational co-host that adds context-aware replies."

    def should_handle(self, author: str, message: str) -> bool:
        triggers = ["cohost", "host", "topic", "what are we doing", "explain"]
        return any(t in message.lower() for t in triggers)

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        # Lightweight persona-based response using existing agent instruction as streamer voice
        streamer = context.get("streamer_profile", {}).get("Name", "the streamer")
        topic = context.get("current_game") or context.get("stream_topic")
        if topic:
            return f"Quick recap: We're live with {topic}. Stick around—I'll keep chat flowing while {streamer} focuses!"
        return f"I'm co-hosting—keeping vibes up and questions answered while {streamer} streams!"