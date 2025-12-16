"""
Advanced Valorant commands for YouTube Chat Bot
"""

from .command import BaseCommand, CommandContext
from typing import Optional
import logging
try:
    from app.logger import get_logger
    from app.valorant_api import get_valorant_api
except ModuleNotFoundError:
    from logger import get_logger
    from valorant_api import get_valorant_api

logger = get_logger(__name__)


class ValorantStatsCommand(BaseCommand):
    """Query Valorant player stats"""
    
    name = "val"
    aliases = ["valorant", "stats"]
    description = "Get Valorant stats: !val stats [username] or !val rank [username]"
    usage = "!val stats username#TAG or !val rank username#TAG"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute valorant stats command"""
        args = self.parse_args(context.message)
        
        if not args:
            return "Usage: !val [stats|rank|agent] [username#TAG] or !val username#TAG"
        
        # Parse command format: !val [query_type] [username#tag]
        query_type = "summary"
        username_tag = None
        
        if len(args) == 1:
            # !val username#TAG
            username_tag = args[0]
        elif len(args) >= 2:
            # !val [stats|rank|agent] username#TAG
            if args[0].lower() in ["stats", "rank", "agent"]:
                query_type = args[0].lower()
                username_tag = args[1]
            else:
                username_tag = args[0]
        
        if not username_tag or "#" not in username_tag:
            return "Invalid format. Use: !val username#TAG (e.g., !val Player#123)"
        
        # Split username and tag
        try:
            username, tag = username_tag.split("#")
        except ValueError:
            return "Invalid format. Use username#TAG"
        
        logger.info(f"Valorant stats query from {context.author}: {username}#{tag} ({query_type})")
        
        # Get region from streamer profile or default to 'eu'
        region = context.streamer_profile.get("Valorant Region", "eu") if context.streamer_profile else "eu"
        
        # Get Valorant API instance
        api = get_valorant_api()
        
        try:
            if query_type in ["rank", "summary"]:
                # Fetch MMR (rank) data
                mmr_data = await api.get_mmr(region, username, tag)
                
                if not mmr_data:
                    return f"❌ Could not find stats for {username}#{tag}. Check spelling and region!"
                
                # Format and return rank info
                response = api.format_rank_response(mmr_data, username, tag)
                
                # If summary, also add recent match
                if query_type == "summary":
                    match_data = await api.get_match_history(region, username, tag, size=1)
                    if match_data:
                        match_summary = api.format_match_summary(match_data, username, tag)
                        response += f"\n{match_summary}"
                
                return response
                
            elif query_type == "stats":
                # Fetch recent matches
                match_data = await api.get_match_history(region, username, tag, size=5)
                
                if not match_data:
                    return f"❌ No recent matches found for {username}#{tag}"
                
                # Calculate average stats
                total_kills = 0
                total_deaths = 0
                total_matches = 0
                wins = 0
                
                for match in match_data:
                    players = match.get("players", {}).get("all_players", [])
                    for player in players:
                        if player.get("name", "").lower() == username.lower():
                            stats = player.get("stats", {})
                            total_kills += stats.get("kills", 0)
                            total_deaths += stats.get("deaths", 0)
                            total_matches += 1
                            
                            # Check if won
                            team = player.get("team", "").lower()
                            teams = match.get("teams", {})
                            if team in teams and teams[team].get("has_won", False):
                                wins += 1
                            break
                
                if total_matches == 0:
                    return f"❌ No match data found for {username}#{tag}"
                
                avg_kills = round(total_kills / total_matches, 1)
                avg_deaths = round(total_deaths / total_matches, 1)
                win_rate = round((wins / total_matches) * 100)
                
                return f"📊 {username}#{tag} (Last {total_matches} games)\nAvg K/D: {avg_kills}/{avg_deaths} | Win Rate: {win_rate}% ({wins}W {total_matches-wins}L)"
            
            else:
                return f"Unknown query type. Use: !val username#TAG [rank/stats]"
                
        except Exception as e:
            logger.error(f"Error fetching Valorant stats: {e}", exc_info=True)
            return f"❌ Error fetching stats for {username}#{tag}. Try again later!"


class ValorantAgentCommand(BaseCommand):
    """Show Valorant agent info"""
    
    name = "agent"
    aliases = ["agents", "champions"]
    description = "Show information about a Valorant agent"
    usage = "!agent [agent_name] or !agents for list"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute agent info command"""
        args = self.parse_args(context.message)
        
        if not args or args[0].lower() in ["list", "all"]:
            agents = [
                "Reyna", "Jett", "Phoenix", "Sage", "Omen", "Brimstone",
                "Cypher", "Killjoy", "Viper", "Sova", "Yoru", "Astra",
                "Skye", "Chamber", "Neon", "Fade", "Gekko", "Harbor", "Iso", "Clove"
            ]
            return f"Valorant agents: {', '.join(agents)}"
        
        agent_name = args[0].lower()
        
        # Agent info database (simplified)
        agent_info = {
            "reyna": "Reyna (Duelist) - Aggressive player with abilities to heal and dismiss herself",
            "jett": "Jett (Duelist) - Fast, mobile agent with dash and projectile abilities",
            "phoenix": "Phoenix (Duelist) - Utility-focused duelist with fire abilities",
            "sage": "Sage (Sentinel) - Support/healer with slow orb and resurrection",
            "omen": "Omen (Controller) - Smoke controller with shadow abilities",
        }
        
        if agent_name in agent_info:
            logger.debug(f"Agent info requested: {agent_name}")
            return agent_info[agent_name]
        else:
            return f"Agent '{agent_name}' not found. Use !agents for full list."


class ValorantMapCommand(BaseCommand):
    """Show Valorant map info"""
    
    name = "map"
    aliases = ["maps"]
    description = "Show Valorant map information"
    usage = "!map [map_name] or !maps for list"
    
    async def execute(self, context: CommandContext) -> Optional[str]:
        """Execute map command"""
        args = self.parse_args(context.message)
        
        maps = ["Ascent", "Bind", "Haven", "Split", "Icebox", "Breeze", "Fracture", "Pearl", "Sunset"]
        
        if not args or args[0].lower() in ["list", "all"]:
            return f"Valorant maps: {', '.join(maps)}"
        
        requested_map = args[0].lower()
        if any(m.lower() == requested_map for m in maps):
            logger.debug(f"Map info requested: {requested_map}")
            return f"Map: {requested_map.capitalize()} - Try !map [map_name] for strategies"
        else:
            return f"Map '{requested_map}' not found. Available: {', '.join(maps)}"
