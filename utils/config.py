import os
import json
from dotenv import load_dotenv

# Load environment variables for sensitive keys
load_dotenv()

# Path to the config file
CONFIG_FILE = 'config.json'

# Dictionary to store configuration
_config = {}

def load_config():
    """Load configuration from config.json and .env files"""
    global _config

    # Load configuration from config.json
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            _config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config.json: {e}")
        _config = {}

    # Add sensitive keys from .env
    sensitive_keys = [
        'DISCORD_TOKEN',
        'YOUTUBE_API_KEY',
        'GEMINI_API_KEY',
        'OPENROUTER_API_KEY',
        'DEEPSEEK_API_KEY'
    ]

    for key in sensitive_keys:
        value = os.getenv(key)
        if value:
            _config[key] = value

def get(key, default=None):
    """Get a configuration value"""
    return _config.get(key, default)

def get_int(key, default=0):
    """Get a configuration value as an integer"""
    try:
        return int(_config.get(key, default))
    except (ValueError, TypeError):
        print(f"Warning: Invalid integer value for {key} in configuration")
        return default

def get_float(key, default=0.0):
    """Get a configuration value as a float"""
    try:
        return float(_config.get(key, default))
    except (ValueError, TypeError):
        print(f"Warning: Invalid float value for {key} in configuration")
        return default

def get_bool(key, default=False):
    """Get a configuration value as a boolean"""
    value = _config.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'y')
    return bool(value)

def set(key, value):
    """Set a configuration value (in memory only)"""
    _config[key] = value

def save():
    """Save configuration to config.json"""
    # Filter out sensitive keys
    sensitive_keys = [
        'DISCORD_TOKEN',
        'YOUTUBE_API_KEY',
        'GEMINI_API_KEY',
        'OPENROUTER_API_KEY',
        'DEEPSEEK_API_KEY'
    ]

    save_config = {k: v for k, v in _config.items() if k not in sensitive_keys}

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config.json: {e}")
        return False

# Load configuration when module is imported
load_config()
