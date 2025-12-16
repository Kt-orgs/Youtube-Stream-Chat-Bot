"""
Shared constants and patterns for the YouTube Chat Bot
"""

import re

# Greeting words
GREETING_WORDS = ["hi", "hello", "hey", "namaste", "namaskar", "hii", "hlo"]

# Hype triggers
HYPE_TRIGGERS = ["gg", "clutch", "win", "pog", "let's go", "fire", "insane"]

# Stats triggers
STATS_TRIGGERS = ["stats", "stream stats", "show stats", "!stats"]

# Gaming keywords
SPECS_KEYWORDS = ["specs", "pc", "system", "gpu", "cpu", "ram", "setup", "config"]
HELP_KEYWORDS = ["help", "madad", "question", "sawal", "puch"]
QUESTION_MARKERS = ["?", "kya", "kaise", "kab", "kahan", "kyun", "what", "why", "how", "who", "when", "where"]

# Community engagement triggers
COMMUNITY_TRIGGERS = ["love", "awesome", "great", "nice", "cool", "vibe", "fun", "enjoy", "favorite", "best", "amazing", "good map", "good game", "gg"]

# Valorant agents (for agent performance queries)
VALORANT_AGENTS = [
    "reyna", "jett", "phoenix", "sage", "omen", "brimstone", "cypher", "killjoy", 
    "viper", "sova", "yoru", "astra", "skye", "chamber", "neon", "fade", "gekko", 
    "harbor", "iso", "clove"
]

# Valorant regions
VALORANT_REGIONS = ["ap", "na", "eu", "kr", "latam", "br"]

# Compiled regex patterns
VALORANT_ID_PATTERN = re.compile(
    r'(?:my\s+id\s+is|id:|riot\s+id\s+is|valorant\s+id\s+is)\s*([a-zA-Z0-9]+)#([a-zA-Z0-9]+)',
    re.IGNORECASE
)

# File paths (relative to app directory)
DATA_DIR = "./data"
PROCESSED_MESSAGES_FILE = f"{DATA_DIR}/processed_messages.txt"
VALORANT_RANK_FILE = f"{DATA_DIR}/valorant_rank.txt"
VALORANT_LAST_GAME_FILE = f"{DATA_DIR}/valorant_last_game.txt"
STREAMER_PROFILE_FILE = "./streamer_profile.json"

# Rate limiting (seconds)
COMMUNITY_ENGAGEMENT_MIN_GAP = 180
GROWTH_BOOSTER_MIN_GAP = 180

# Response delays
RESPONSE_DELAY_SECONDS = 2.0

# Periodic tasks
STATS_POSTING_INTERVAL = 900  # 15 minutes
