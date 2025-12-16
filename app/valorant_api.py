"""
Valorant API Integration using HenrikDev API
Provides real-time player stats, ranks, and match data
"""

import os
import aiohttp
import logging
from typing import Optional, Dict, Any
try:
    from app.logger import get_logger
except ModuleNotFoundError:
    from logger import get_logger

logger = get_logger(__name__)


class ValorantAPI:
    """Wrapper for HenrikDev Valorant API"""
    
    BASE_URL = "https://api.henrikdev.xyz/valorant"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Valorant API client
        
        Args:
            api_key: HenrikDev API key (optional, but recommended for rate limits)
        """
        self.api_key = api_key or os.getenv("HENRIK_DEV_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["Authorization"] = self.api_key
            logger.info("Valorant API initialized with API key")
        else:
            logger.warning("Valorant API initialized without API key (limited rate)")
    
    async def get_account(self, name: str, tag: str) -> Optional[Dict[str, Any]]:
        """
        Get account information
        
        Args:
            name: Player name
            tag: Player tag
            
        Returns:
            Account data or None if error
        """
        url = f"{self.BASE_URL}/v1/account/{name}/{tag}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Account data retrieved for {name}#{tag}")
                        return data.get("data")
                    elif response.status == 404:
                        logger.info(f"Account not found: {name}#{tag}")
                        return None
                    else:
                        logger.error(f"API error {response.status}: {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching account: {e}")
            return None
    
    async def get_mmr(self, region: str, name: str, tag: str) -> Optional[Dict[str, Any]]:
        """
        Get MMR (rank) information
        
        Args:
            region: Region (eu, na, ap, kr, latam, br)
            name: Player name
            tag: Player tag
            
        Returns:
            MMR data or None if error
        """
        url = f"{self.BASE_URL}/v2/mmr/{region}/{name}/{tag}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"MMR data retrieved for {name}#{tag}")
                        return data.get("data")
                    elif response.status == 404:
                        logger.info(f"MMR not found: {name}#{tag}")
                        return None
                    else:
                        logger.error(f"API error {response.status}: {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching MMR: {e}")
            return None
    
    async def get_match_history(self, region: str, name: str, tag: str, mode: str = "competitive", size: int = 5) -> Optional[Dict[str, Any]]:
        """
        Get match history
        
        Args:
            region: Region (eu, na, ap, kr, latam, br)
            name: Player name
            tag: Player tag
            mode: Game mode (competitive, unrated, deathmatch, etc.)
            size: Number of matches (1-20)
            
        Returns:
            Match history data or None if error
        """
        url = f"{self.BASE_URL}/v3/matches/{region}/{name}/{tag}"
        params = {"mode": mode, "size": min(size, 20)}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Match history retrieved for {name}#{tag}")
                        return data.get("data")
                    elif response.status == 404:
                        logger.info(f"Match history not found: {name}#{tag}")
                        return None
                    else:
                        logger.error(f"API error {response.status}: {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching match history: {e}")
            return None
    
    def format_rank_response(self, mmr_data: Dict[str, Any], name: str, tag: str) -> str:
        """
        Format rank data into a chat-friendly response
        
        Args:
            mmr_data: MMR data from API
            name: Player name
            tag: Player tag
            
        Returns:
            Formatted rank string
        """
        try:
            current_data = mmr_data.get("current_data", {})
            
            # Get rank info
            current_tier = current_data.get("currenttierpatched", "Unranked")
            rr = current_data.get("ranking_in_tier", 0)
            elo = current_data.get("elo", 0)
            
            # Get change info
            mmr_change = mmr_data.get("mmr_change_to_last_game", 0)
            
            response = f"🎮 {name}#{tag}\n"
            response += f"Rank: {current_tier}"
            
            if current_tier != "Unranked":
                response += f" ({rr} RR)"
            
            if mmr_change != 0:
                change_symbol = "+" if mmr_change > 0 else ""
                response += f" | Last game: {change_symbol}{mmr_change} RR"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting rank response: {e}")
            return f"Error formatting stats for {name}#{tag}"
    
    def format_match_summary(self, match_data: list, name: str, tag: str) -> str:
        """
        Format recent matches into a summary
        
        Args:
            match_data: List of recent matches
            name: Player name  
            tag: Player tag
            
        Returns:
            Formatted match summary
        """
        try:
            if not match_data or len(match_data) == 0:
                return f"No recent matches found for {name}#{tag}"
            
            recent_match = match_data[0]
            
            # Find player's stats in the match
            players = recent_match.get("players", {}).get("all_players", [])
            player_stats = None
            
            for player in players:
                if player.get("name", "").lower() == name.lower() and player.get("tag", "").lower() == tag.lower():
                    player_stats = player
                    break
            
            if not player_stats:
                return f"Stats not found in recent match for {name}#{tag}"
            
            # Extract stats
            kills = player_stats.get("stats", {}).get("kills", 0)
            deaths = player_stats.get("stats", {}).get("deaths", 0)
            assists = player_stats.get("stats", {}).get("assists", 0)
            
            kd_ratio = round(kills / deaths, 2) if deaths > 0 else kills
            
            # Get match info
            map_name = recent_match.get("metadata", {}).get("map", "Unknown")
            agent = player_stats.get("character", "Unknown")
            
            # Team result
            team = player_stats.get("team", "").lower()
            teams_data = recent_match.get("teams", {})
            won = False
            
            if team in teams_data:
                won = teams_data[team].get("has_won", False)
            
            result = "🏆 WIN" if won else "❌ LOSS"
            
            response = f"{result} | Last game on {map_name}\n"
            response += f"Agent: {agent} | K/D/A: {kills}/{deaths}/{assists} ({kd_ratio} KD)"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting match summary: {e}")
            return f"Error formatting match data for {name}#{tag}"


# Singleton instance
_valorant_api = None

def get_valorant_api() -> ValorantAPI:
    """Get singleton Valorant API instance"""
    global _valorant_api
    if _valorant_api is None:
        _valorant_api = ValorantAPI()
    return _valorant_api
