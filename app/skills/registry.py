from typing import List, Dict, Any
from .skills import BaseSkill


class SkillRegistry:
    def __init__(self):
        self._skills: List[BaseSkill] = []

    def register(self, skill: BaseSkill):
        self._skills.append(skill)

    def list(self) -> List[BaseSkill]:
        return list(self._skills)

    async def dispatch(self, author: str, message: str, context: Dict[str, Any]) -> str | None:
        for skill in self._skills:
            try:
                if skill.should_handle(author, message):
                    return await skill.handle(author, message, context)
            except Exception:
                # Fail-safe: skip misbehaving skills
                continue
        return None