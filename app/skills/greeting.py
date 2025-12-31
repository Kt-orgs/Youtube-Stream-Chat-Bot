import logging
from typing import Optional, Dict, Any
from .skills import BaseSkill
try:
    from app.constants import GREETING_WORDS
    from app.logger import get_logger
except ModuleNotFoundError:
    from constants import GREETING_WORDS
    from logger import get_logger

logger = get_logger(__name__)


class GreetingSkill(BaseSkill):
    name = "greeting"
    description = "Welcomes viewers who greet or say hello with a friendly message."

    def should_handle(self, author: str, message: str) -> bool:
        msg = message.lower().strip()
        # Trigger if message is a greeting or starts with greeting word
        return any(msg == g or msg.startswith(g + " ") for g in GREETING_WORDS)

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        msg = message.strip()
        # Mirror the greeting if present, otherwise default to Hello
        lower = msg.lower()
        greet_map = {
            "hello": "Hello",
            "hi": "Hi",
            "hey": "Hey",
            "namaste": "Namaste",
            "namaskar": "Namaskar",
            "hii": "Hi",
            "hlo": "Hello",
        }
        greeting = "Hello"
        for k, v in greet_map.items():
            if lower.startswith(k):
                greeting = v
                break
        streamer = context.get("streamer_profile", {}).get("Name", "the stream")
        # Keep it short and welcoming
        response = f"{greeting} {author}! Welcome to the stream—glad you're here. Tag me with @StreamNova if you have any questions!"
        logger.debug(f"Greeting skill triggered for {author}")
        return response