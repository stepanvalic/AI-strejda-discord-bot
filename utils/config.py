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

        # Zajistíme, že boolean hodnoty jsou správně převedeny z JSON na Python
        # JSON používá true/false, Python používá True/False
        for key, value in _config.items():
            if isinstance(value, bool):
                # Hodnota je už boolean, ale ujistíme se, že je to Python boolean
                _config[key] = bool(value)

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

    # Debug výpis pro kontrolu boolean hodnot
    for key, value in _config.items():
        if isinstance(value, bool):
            print(f"Boolean config: {key} = {value} (type: {type(value).__name__})")

def get(key, default=None):
    """Get a configuration value"""
    if key not in _config:
        print(f"Warning: Key '{key}' not found in configuration, using default: {default}")
        return default
    return _config.get(key)

def get_int(key, default=0):
    """Get a configuration value as an integer"""
    if key not in _config:
        print(f"Warning: Key '{key}' not found in configuration, using default: {default}")
        return default

    try:
        return int(_config.get(key))
    except (ValueError, TypeError):
        print(f"Warning: Invalid integer value for {key} in configuration")
        return default

def get_float(key, default=0.0):
    """Get a configuration value as a float"""
    if key not in _config:
        print(f"Warning: Key '{key}' not found in configuration, using default: {default}")
        return default

    try:
        return float(_config.get(key))
    except (ValueError, TypeError):
        print(f"Warning: Invalid float value for {key} in configuration")
        return default

def get_bool(key, default=False):
    """Get a configuration value as a boolean"""
    if key not in _config:
        print(f"Warning: Key '{key}' not found in configuration, using default: {default}")
        return default

    value = _config.get(key)

    # JSON true/false jsou automaticky převedeny na Python True/False při načtení pomocí json.load()
    # Tato funkce zajišťuje, že hodnoty jsou správně převedeny na Python boolean

    # Pokud je hodnota už boolean, vrátíme ji přímo
    if isinstance(value, bool):
        return value

    # Pokud je hodnota string, zkontrolujeme, zda odpovídá true/yes/1/y
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'y')

    # Pro ostatní typy použijeme standardní Python bool()
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

    # Ujistíme se, že boolean hodnoty jsou správně převedeny z Python na JSON
    # Python používá True/False, JSON používá true/false
    # json.dump() automaticky převede Python True/False na JSON true/false

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_config, f, indent=4)

        # Debug výpis pro kontrolu uložených hodnot
        print("Configuration saved successfully")
        for key, value in save_config.items():
            if isinstance(value, bool):
                print(f"Saved boolean config: {key} = {value}")

        return True
    except Exception as e:
        print(f"Error saving config.json: {e}")
        return False

# Load configuration when module is imported
load_config()
