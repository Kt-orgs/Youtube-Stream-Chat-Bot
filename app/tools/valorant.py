import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_valorant_stats(username: str, tag: str, region: str = 'ap', query_type: str = 'summary', agent: str = None) -> str:
    """
    Fetches Valorant stats for a player using HenrikDev API.
    
    Args:
        username: The Riot ID username (e.g., "Loki").
        tag: The Riot ID tag (e.g., "1234"). Do not include the '#'.
        region: The region code (ap, na, eu, kr, latam, br). Default is 'ap'.
        query_type: Type of stats to fetch. 'summary' for rank/last match, 'agent_performance' for specific agent stats.
        agent: The agent name (e.g., "Reyna") if query_type is 'agent_performance'.
        
    Returns:
        A string summary of the requested stats.
    """
    api_key = os.environ.get("HENRIK_DEV_API_KEY")
    
    if not api_key:
        return "Configuration Error: HENRIK_DEV_API_KEY is missing. Please add your API key to the .env file."

    # Base URL for HenrikDev API
    base_url = "https://api.henrikdev.xyz"
    
    headers = {}
    if api_key:
        headers["Authorization"] = api_key
    
    try:
        # --- AGENT PERFORMANCE LOGIC ---
        if query_type == 'agent_performance':
            if not agent:
                return "Error: Agent name is required for agent performance stats."
                
            # Use lifetime matches endpoint to scan recent history (last 30 matches)
            matches_url = f"{base_url}/valorant/v1/lifetime/matches/{region}/{username}/{tag}?size=30"
            print(f"Fetching Lifetime Matches for Agent Stats: {matches_url}")
            
            response = requests.get(matches_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return f"Error fetching match history: {response.status_code}"
                
            data = response.json()
            matches = data.get('data', [])
            
            if not matches:
                return "No recent matches found."
                
            highest_kills = -1
            best_match = None
            matches_played = 0
            
            target_agent = agent.lower()
            
            for match in matches:
                stats = match.get('stats', {})
                character = stats.get('character', {}).get('name', 'Unknown')
                
                if character.lower() != target_agent:
                    continue
                    
                kills = stats.get('kills', 0)
                matches_played += 1
                
                if kills > highest_kills:
                    highest_kills = kills
                    best_match = match
            
            if matches_played == 0:
                return f"No matches found with {agent} in the last 30 games."
            
            # Format result
            result_agent = best_match['stats']['character']['name']
            map_name = best_match['meta']['map']['name']
            k = best_match['stats']['kills']
            d = best_match['stats']['deaths']
            a = best_match['stats']['assists']
            
            return f"Highest kills with {result_agent} (last 30 games): {k} kills ({k}/{d}/{a}) on {map_name}."

        # --- SUMMARY LOGIC (Rank + Last Match) ---
        else:
            # 1. Get MMR (Rank info)
            mmr_url = f"{base_url}/valorant/v1/mmr/{region}/{username}/{tag}"
            print(f"Fetching Valorant MMR: {mmr_url}")
            
            mmr_response = requests.get(mmr_url, headers=headers, timeout=10)
            
            if mmr_response.status_code == 401:
                return "API Error: Unauthorized (401). Your HENRIK_DEV_API_KEY is invalid or expired."
            
            rank_info = "Rank: Unknown"
            elo = "N/A"
            
            if mmr_response.status_code == 200:
                data = mmr_response.json().get("data", {})
                current_tier = data.get("currenttierpatched", "Unrated")
                ranking_in_tier = data.get("ranking_in_tier", 0)
                elo = data.get("elo", 0)
                rank_info = f"{current_tier} ({ranking_in_tier} RR)"
            elif mmr_response.status_code == 404:
                return f"Player {username}#{tag} not found in region {region}. Please check the name and tag."
            else:
                print(f"MMR API Error: {mmr_response.status_code} - {mmr_response.text}")
                
            # 2. Get Last Match Stats
            matches_url = f"{base_url}/valorant/v3/matches/{region}/{username}/{tag}?size=1"
            print(f"Fetching Last Match: {matches_url}")
            
            matches_response = requests.get(matches_url, headers=headers, timeout=10)
            
            last_match_info = "No recent matches found."
            
            if matches_response.status_code == 200:
                match_data = matches_response.json()
                if match_data.get("data") and len(match_data["data"]) > 0:
                    last_match = match_data["data"][0]
                    metadata = last_match.get("metadata", {})
                    map_name = metadata.get("map", "Unknown Map")
                    mode = metadata.get("mode", "Unknown Mode")
                    
                    # Find player stats
                    all_players = last_match.get("players", {}).get("all_players", [])
                    player = next((p for p in all_players 
                                 if p.get("name", "").lower() == username.lower() 
                                 and p.get("tag", "").lower() == tag.lower()), None)
                    
                    if player:
                        agent_name = player.get("character", "Unknown Agent")
                        stats = player.get("stats", {})
                        k = stats.get("kills", 0)
                        d = stats.get("deaths", 0)
                        a = stats.get("assists", 0)
                        
                        # Determine result
                        winning_team = ""
                        teams = last_match.get("teams", {})
                        if teams.get("red", {}).get("has_won"):
                            winning_team = "red"
                        elif teams.get("blue", {}).get("has_won"):
                            winning_team = "blue"
                        
                        team = player.get("team", "").lower()
                        result = "Won" if team == winning_team else "Lost"
                        
                        last_match_info = f"{result} on {map_name} ({mode}) as {agent_name}. KDA: {k}/{d}/{a}."
            
            return f"Valorant Stats for {username}#{tag}:\nCurrent Rank: {rank_info}\nELO: {elo}\nLast Match: {last_match_info}"
        
    except Exception as e:
        return f"Error fetching Valorant stats: {str(e)}"
