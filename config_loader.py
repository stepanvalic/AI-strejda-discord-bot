"""
Configuration loader for the Discord bot.
This module loads configuration from config.json and environment variables.
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file (for API keys)
load_dotenv()

# Load configuration from JSON file
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# Load the configuration
_config = load_config()

# Discord Configuration
def get_discord_config():
    return _config['discord']

def get_guild_id():
    return _config['discord']['guild_id']

def get_welcome_channel_id():
    return _config['discord']['welcome_channel_id']

def get_discord_token():
    return os.getenv("DISCORD_TOKEN", "")

# Bot Activity Configuration
def get_activity_config():
    return _config['bot_activity']

def get_activity_base_text():
    return _config['bot_activity']['base_text']

def get_activity_format_text():
    return _config['bot_activity']['format_text']

# YouTube Configuration
def get_youtube_config():
    return _config['youtube']

def get_youtube_channel_id():
    return _config['youtube']['channel_id']

def get_youtube_notification_channel_id():
    return _config['youtube']['notification_channel_id']

def get_youtube_api_key():
    return os.getenv("YOUTUBE_API_KEY", "")

def get_youtube_check_interval():
    return _config['youtube']['check_interval_seconds']

# Counting Game Configuration
def get_counting_config():
    return _config['counting_game']

def get_counting_channel_id():
    return _config['counting_game']['channel_id']

def get_counting_save_file():
    return _config['counting_game']['save_file']

def get_counting_topic_prefix():
    return _config['counting_game']['topic_prefix']

# AI Moderation Configuration
def get_ai_moderation_config():
    return _config['ai_moderation']

def get_ai_model():
    return _config['ai_moderation']['model']

def get_ai_messages_batch():
    return _config['ai_moderation']['messages_batch']

def get_ai_moderation_save_file():
    return _config['ai_moderation']['save_file']

def get_ai_moderation_interval():
    return _config['ai_moderation']['interval_minutes']

def get_gemini_api_key():
    return os.getenv("GEMINI_API_KEY", "")

def get_ai_positive_thresholds():
    return _config['ai_moderation']['positive_thresholds']

def get_ai_negative_thresholds():
    return _config['ai_moderation']['negative_thresholds']

def get_ai_negative_penalty():
    return _config['ai_moderation']['negative_penalty']

def get_ai_role_ids():
    return _config['ai_moderation']['role_ids']

# Audit Log Configuration
def get_audit_log_channel_id():
    return _config['audit_log']['channel_id']

# Chat Summary Configuration
def get_chat_summary_config():
    return _config['chat_summary']

def get_openrouter_model():
    return _config['chat_summary']['model']

def get_summary_chat_id():
    return _config['chat_summary']['chat_id']

def get_summary_channel_id():
    return _config['chat_summary']['channel_id']

def get_openrouter_api_key():
    return os.getenv("OPENROUTER_API_KEY", "")

# Logger Configuration
def get_logger_config():
    return _config['logger']

def get_log_level():
    return _config['logger']['level']

def get_log_max_size():
    return _config['logger']['max_size']

def get_log_backup_count():
    return _config['logger']['backup_count']
