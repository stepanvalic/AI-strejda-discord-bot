import os
import json
from datetime import datetime

DB_PATH = "db/youtube_videos.json"

def ensure_db_exists():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({"videos": []}, f, ensure_ascii=False, indent=2)

def _load_db():
    ensure_db_exists()

    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"videos": []}

def _save_db(db_data):
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

def save_video(video_data, message_id=None, channel_message_id=None):
    db = _load_db()
    videos = db["videos"]

    now = datetime.now().isoformat()

    existing_video = None
    for i, video in enumerate(videos):
        if video.get("video_id") == video_data['id']:
            existing_video = video
            existing_index = i
            break

    if existing_video:
        update_data = {
            "title": video_data['title'],
            "description": video_data['description'],
            "thumbnail_url": video_data['thumbnail'],
            "channel_title": video_data['channel_title'],
            "views": int(video_data['views']),
            "likes": int(video_data['likes']),
            "comments": int(video_data['comments']),
            "last_updated": now
        }

        # Přidáme informace o live streamu, pokud existují
        if 'is_live' in video_data:
            update_data["is_live"] = video_data['is_live']

        if 'scheduled_start_time' in video_data and video_data['scheduled_start_time']:
            update_data["scheduled_start_time"] = video_data['scheduled_start_time']

        if 'actual_start_time' in video_data and video_data['actual_start_time']:
            update_data["actual_start_time"] = video_data['actual_start_time']

        videos[existing_index].update(update_data)
    else:
        new_video = {
            "video_id": video_data['id'],
            "title": video_data['title'],
            "description": video_data['description'],
            "thumbnail_url": video_data['thumbnail'],
            "published_at": video_data['published_at'],
            "channel_title": video_data['channel_title'],
            "duration": video_data['duration'],
            "views": int(video_data['views']),
            "likes": int(video_data['likes']),
            "comments": int(video_data['comments']),
            "message_id": message_id,
            "channel_message_id": channel_message_id,
            "announced_at": now if message_id else None,
            "last_updated": now
        }

        # Přidáme informace o live streamu, pokud existují
        if 'is_live' in video_data:
            new_video["is_live"] = video_data['is_live']

        if 'scheduled_start_time' in video_data and video_data['scheduled_start_time']:
            new_video["scheduled_start_time"] = video_data['scheduled_start_time']

        if 'actual_start_time' in video_data and video_data['actual_start_time']:
            new_video["actual_start_time"] = video_data['actual_start_time']
        videos.append(new_video)

    _save_db(db)

def get_video(video_id):
    db = _load_db()

    for video in db["videos"]:
        if video.get("video_id") == video_id:
            return video

    return None

def get_all_videos():
    db = _load_db()

    return sorted(db["videos"], key=lambda x: x.get("published_at", ""), reverse=True)

def get_announced_videos():
    db = _load_db()

    announced = [v for v in db["videos"] if v.get("message_id")]

    return sorted(announced, key=lambda x: x.get("announced_at", ""), reverse=True)

def update_message_ids(video_id, message_id, channel_message_id):
    db = _load_db()

    now = datetime.now().isoformat()

    for video in db["videos"]:
        if video.get("video_id") == video_id:
            video["message_id"] = message_id
            video["channel_message_id"] = channel_message_id
            video["announced_at"] = now
            break

    _save_db(db)

def is_video_announced(video_id):
    video = get_video(video_id)

    return video is not None and video.get("message_id") is not None
