from typing import Optional, Dict, Any
import logging
try:
    from app.skills.skills import BaseSkill
    from app.tools.valorant import get_valorant_stats
    from app.constants import VALORANT_AGENTS, VALORANT_ID_PATTERN
    from app.utils.file_utils import save_stats_to_file
except ModuleNotFoundError:
    from skills.skills import BaseSkill
    from tools.valorant import get_valorant_stats
    from constants import VALORANT_AGENTS, VALORANT_ID_PATTERN
    from utils.file_utils import save_stats_to_file

logger = logging.getLogger(__name__)

class ValorantStatsSkill(BaseSkill):
    name = "valorant_stats"
    description = "Answers Valorant stat questions using the Valorant API."

    def should_handle(self, author: str, message: str) -> bool:
        msg = message.lower()
        # Ignore bot's own Valorant stats replies
        if msg.startswith("valorant stats for"):
            return False
        # Trigger on KD, aces, rank, last match, agent performance
        triggers = ["kd", "k/d", "aces", "rank", "last match", "stats", "valorant"]
        return any(t in msg for t in triggers)

    async def handle(self, author: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        profile = context.get("streamer_profile", {})
        valorant_id = profile.get("Valorant ID", None)
        region = profile.get("Valorant Region", "eu")
        
        logger.info(f"[ValorantStatsSkill] Profile Valorant ID: {valorant_id}, Region: {region}")
        
        # Try to extract Valorant ID from message if present
        msg = message.lower()
        match = VALORANT_ID_PATTERN.search(message)
        if match:
            username, tag = match.group(1), match.group(2)
            logger.info(f"Extracted Valorant ID from message: {username}#{tag}")
        elif valorant_id and "#" in valorant_id:
            username, tag = valorant_id.split("#", 1)
            logger.info(f"Using streamer's Valorant ID from profile: {username}#{tag}")
        else:
            logger.warning(f"No Valorant ID in message or profile. Profile ID = {valorant_id}")
            return "Valorant ID not found. Use !val YourName#TAG or set streamer Valorant ID in profile."
        
        stats = None
        # KD or aces
        if "kd" in msg or "k/d" in msg:
            logger.info(f"Fetching KD stats for {username}#{tag}")
            stats = get_valorant_stats(username, tag, region, query_type="summary")
        elif "aces" in msg:
            # For simplicity, use agent_performance for all agents (could be improved)
            stats = "Ace count lookup not implemented yet."
        elif "rank" in msg:
            full_stats = get_valorant_stats(username, tag, region, query_type="summary")
            # Extract only the rank line
            rank_line = None
            last_match_line = None
            for line in full_stats.splitlines():
                if line.lower().startswith("current rank:"):
                    rank_line = line.strip()
                if line.lower().startswith("last match:"):
                    last_match_line = line.strip()
            if rank_line:
                stats = rank_line
            else:
                stats = "Rank info not found."
            # Save rank and last match to separate files
            if rank_line or last_match_line:
                save_stats_to_file(rank_line or "", last_match_line or "")
                logger.info(f"Saved Valorant stats for {username}#{tag} to files")
            return stats
        elif "last match" in msg or "stats" in msg:
            full_stats = get_valorant_stats(username, tag, region, query_type="summary")
            # Extract only the last match line
            last_match_line = None
            rank_line = None
            for line in full_stats.splitlines():
                if line.lower().startswith("last match:"):
                    last_match_line = line.strip()
                if line.lower().startswith("current rank:"):
                    rank_line = line.strip()
            if last_match_line:
                stats = last_match_line
            else:
                stats = "Last match info not found."
            # Save rank and last match to separate files
            if rank_line or last_match_line:
                save_stats_to_file(rank_line or "", last_match_line or "")
                logger.info(f"Saved Valorant stats for {username}#{tag} to files")
            return stats
        else:
            # Agent performance (e.g., "Reyna stats")
            for agent in VALORANT_AGENTS:
                if agent in msg:
                    stats = get_valorant_stats(username, tag, region, query_type="agent_performance", agent=agent.title())
                    logger.info(f"Fetched agent stats for {agent} - {username}#{tag}")
                    break
            return stats
