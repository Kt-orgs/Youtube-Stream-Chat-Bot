from typing import Optional, Dict, Any


class BaseSkill:
    name: str = "base"
    description: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def should_handle(self, author: str, message: str) -> bool:
        return False

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        return None