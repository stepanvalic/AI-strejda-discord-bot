"""
Configuration file for the Discord bot.
This file contains all non-sensitive configuration settings.
API keys and tokens are stored in the .env file.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (only for API keys)
load_dotenv()

# Discord Configuration
GUILD_ID = 1359910160277045338
WELCOME_CHANNEL_ID = 1360178791942455337
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# Bot Activity Configuration
ACTIVITY_BASE_TEXT = ""
ACTIVITY_FORMAT_TEXT = "{count} darebáků"

# YouTube Configuration
YOUTUBE_CHANNEL_ID = "@davidstrejc"
YOUTUBE_NOTIFICATION_CHANNEL_ID = 1360172627141988442
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")  # Načítáme z .env
CHECK_INTERVAL_SECONDS = 3600

# Counting Game Configuration
COUNTING_CHANNEL_ID = 1362166632482476292
COUNTING_SAVE_FILE = "db/counting.json"
COUNTING_TOPIC_PREFIX = "Počítejte od 1 do nekonečna. Další číslo:"

# AI Moderation Configuration
AI_MODEL = "gemini-2.0-flash"
AI_MESSAGES_BATCH = 15
AI_MODERATION_SAVE_FILE = "db/ai_moderation.json"
AI_MODERATION_INTERVAL_MINUTES = 30
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Positive score thresholds for role rewards
AI_POSITIVE_THRESHOLD_1 = 800
AI_POSITIVE_THRESHOLD_2 = 2000
AI_POSITIVE_THRESHOLD_3 = 5000

# Negative score thresholds
AI_NEGATIVE_THRESHOLD = -35
AI_VERY_NEGATIVE_THRESHOLD = -1250

# Penalty for very negative messages
AI_NEGATIVE_PENALTY = -30

# Role IDs for different levels
AI_POSITIVE_ROLE_ID_1 = 1362165722955907333
AI_POSITIVE_ROLE_ID_2 = 1362165065368735834
AI_POSITIVE_ROLE_ID_3 = 1362164720215261244
AI_NEGATIVE_ROLE_ID = 1362164949018742805

# Audit Log Configuration
AUDIT_LOG_CHANNEL_ID = 1362167228358856865

# Chat Summary Configuration
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3-0324:free"
SUMMARY_CHAT_ID = 1359910160277045341
SUMMARY_CHANNEL_ID = 1362483597226803270
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Logger Configuration
LOG_LEVEL = "INFO"
LOG_MAX_SIZE = 5242880  # 5MB default
LOG_BACKUP_COUNT = 10
