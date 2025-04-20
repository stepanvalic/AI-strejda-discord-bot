import os
import json
import glob
from datetime import datetime, timedelta

CHAT_DB_PATH = "db/chat_messages.json"
SUMMARY_DIR = "db/sumar"

def ensure_db_exists():
    """Ensure the database file and directories exist"""
    os.makedirs(os.path.dirname(CHAT_DB_PATH), exist_ok=True)
    os.makedirs(SUMMARY_DIR, exist_ok=True)

    if not os.path.exists(CHAT_DB_PATH):
        with open(CHAT_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({"messages": []}, f, ensure_ascii=False, indent=2)

def _load_db():
    """Load the database from file"""
    ensure_db_exists()

    try:
        with open(CHAT_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"messages": [], "summaries": []}

def _save_db(db_data):
    """Save the database to file"""
    with open(CHAT_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

def save_message(message_data):
    """Save a message to the database"""
    db = _load_db()
    messages = db["messages"]

    messages.append(message_data)

    _save_db(db)

def get_messages_by_date(date):
    """Get all messages for a specific date (YYYY-MM-DD)"""
    db = _load_db()

    # Filter messages by date
    date_messages = []
    for msg in db["messages"]:
        timestamp = msg.get("timestamp", "")
        # Kontrola, zda timestamp začíná datem (YYYY-MM-DD)
        if timestamp and timestamp.startswith(date):
            date_messages.append(msg)
        # Pokud je rok 2025, opravíme na 2024 (chyba v časovém razítku)
        elif timestamp and timestamp.startswith("2025") and timestamp[5:].startswith(date[5:]):
            # Vytvoříme kopii zprávy s opraveným časovým razítkem
            fixed_msg = msg.copy()
            fixed_msg["timestamp"] = "2024" + timestamp[4:]
            date_messages.append(fixed_msg)

    print(f"[Summary] Found {len(date_messages)} messages for date {date}")
    return date_messages

def get_messages_since_last_summary():
    """Get all messages since the last summary was created"""
    db = _load_db()

    # Get the timestamp of the last summary
    summaries = db.get("summaries", [])

    if not summaries:
        # If no summaries exist, return all messages
        return db["messages"]

    last_summary = summaries[-1]
    last_summary_time = last_summary.get("timestamp", "")

    # Filter messages that were created after the last summary
    new_messages = [
        msg for msg in db["messages"]
        if msg.get("timestamp", "") > last_summary_time
    ]

    return new_messages

def get_messages_for_day(day_offset=0):
    """Get messages for a specific day (0 = today, -1 = yesterday, etc.)"""
    target_date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y-%m-%d")
    return get_messages_by_date(target_date)

def get_summary_path(date):
    """Get the file path for a summary by date"""
    return os.path.join(SUMMARY_DIR, f"{date}.json")

def save_summary(summary_data):
    """Save a summary to a separate file by date"""
    date = summary_data.get("date")
    if not date:
        raise ValueError("Summary data must include a date")

    # Ensure the summary directory exists
    os.makedirs(SUMMARY_DIR, exist_ok=True)
    print(f"[Summary] Ensuring summary directory exists: {SUMMARY_DIR}")

    # Save the summary to a file named by date
    summary_path = get_summary_path(date)
    print(f"[Summary] Saving summary to file: {summary_path}")

    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        print(f"[Summary] Successfully saved summary for {date} to {summary_path}")
    except Exception as e:
        print(f"[Summary] Error saving summary to file: {e}")
        raise

    return summary_path

def get_latest_summary():
    """Get the latest summary from the summary directory"""
    # Ensure the summary directory exists
    os.makedirs(SUMMARY_DIR, exist_ok=True)

    # Get all summary files
    summary_files = glob.glob(os.path.join(SUMMARY_DIR, "*.json"))

    if not summary_files:
        return None

    # Sort by modification time (newest first)
    latest_file = max(summary_files, key=os.path.getmtime)

    # Load and return the summary
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def get_summary_by_date(date):
    """Get summary for a specific date (YYYY-MM-DD)"""
    summary_path = get_summary_path(date)

    if not os.path.exists(summary_path):
        return None

    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def list_all_summaries():
    """List all available summaries"""
    # Ensure the summary directory exists
    os.makedirs(SUMMARY_DIR, exist_ok=True)

    # Get all summary files
    summary_files = glob.glob(os.path.join(SUMMARY_DIR, "*.json"))

    summaries = []
    for file_path in summary_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                summaries.append(summary)
        except (json.JSONDecodeError, FileNotFoundError):
            continue

    # Sort by date (newest first)
    return sorted(summaries, key=lambda x: x.get("date", ""), reverse=True)

def clean_old_messages(days_to_keep=30):
    """Remove messages older than the specified number of days"""
    db = _load_db()

    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

    # Keep only messages newer than the cutoff date
    db["messages"] = [
        msg for msg in db["messages"]
        if msg.get("timestamp", "") >= cutoff_date
    ]

    _save_db(db)

    return len(db["messages"])
