from typing import Optional, Dict, Any
from .skills import BaseSkill


class GrowthBoosterSkill(BaseSkill):
    name = "growth_booster"
    description = "Light CTA skill that reminds viewers to like/subscribe or share at tasteful intervals."

    def __init__(self, config=None):
        super().__init__(config)
        self._last_ts: float | None = None

    def should_handle(self, author: str, message: str) -> bool:
        # Trigger on positive sentiment words
        triggers = ["love", "awesome", "great", "nice", "good stream", "cool"]
        return any(t in message.lower() for t in triggers)

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        # Rate limit via registry context clock
        import time
        now = time.time()
        min_gap = int(self.config.get("min_gap_seconds", 120))
        if self._last_ts and (now - self._last_ts) < min_gap:
            return None
        self._last_ts = now
        streamer = context.get("streamer_profile", {}).get("Name", "the channel")
        return f"If you’re enjoying, drop a like and consider subscribing to support {streamer}! 💙"