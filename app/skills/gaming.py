from typing import Optional, Dict, Any
from .skills import BaseSkill


class SmartGamingAssistantSkill(BaseSkill):
    name = "smart_gaming_assistant"
    description = "Answers quick gaming questions and shares tips; calls Valorant tool when relevant."

    def should_handle(self, author: str, message: str) -> bool:
        msg = message.lower()
        return any(k in msg for k in ["settings", "sens", "crosshair", "rank", "kd", "rr", "valorant"]) or "tip" in msg

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        msg = message.lower()
        # If Valorant stats requested, defer to main agent by returning None so default path handles it
        if any(k in msg for k in ["rank", "kd", "rr"]) and "valorant" in msg:
            return None
        # Provide concise general tips
        if "sens" in msg or "sensitivity" in msg:
            return "General tip: pick a sens you can track with; avoid changing mid-week—consistency beats micro-optimizing."
        if "crosshair" in msg:
            return "Try a simple crosshair (1-2 thickness, no outlines). Prioritize clarity over style—muscle memory wins."
        if "settings" in msg:
            return "Low shadows, high texture clarity, limit post-processing. Keep FPS stable > input latency matters."
        if "tip" in msg:
            return "Small tip: take 5s resets after bad rounds—breathing + plan beats tilt."
        return None