import os
import json
import requests
import re
from datetime import datetime, timedelta
from utils import config, db

# Načtení YouTube API klíče z .env souboru
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
BASE_URL = 'https://www.googleapis.com/youtube/v3'

# Načtení konfigurace
CHECK_INTERVAL_SECONDS = config.get_int('CHECK_INTERVAL_SECONDS', 5)
NEW_VIDEO_MAX_AGE_HOURS = config.get_int('NEW_VIDEO_MAX_AGE_HOURS', 24)

def get_channel_id(channel_handle):
    """
    Získá ID kanálu z handle (@username) nebo přímo z ID kanálu
    """
    if not channel_handle:
        return None

    # Pokud je to již ID kanálu (začíná na UC), vrátíme ho přímo
    if channel_handle.startswith('UC'):
        return channel_handle

    # Pokud je to handle (začíná na @), získáme ID kanálu z API
    if channel_handle.startswith('@'):
        handle = channel_handle[1:]  # Odstraníme @ ze začátku
        url = f"{BASE_URL}/search?part=snippet&q={handle}&type=channel&key={YOUTUBE_API_KEY}"

        try:
            response = requests.get(url)
            data = response.json()

            if 'items' in data and len(data['items']) > 0:
                return data['items'][0]['snippet']['channelId']
        except Exception as e:
            print(f"Chyba při získávání ID kanálu pro {channel_handle}: {e}")

    # Pokud je to custom URL, získáme ID kanálu z API
    url = f"{BASE_URL}/search?part=snippet&q={channel_handle}&type=channel&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['snippet']['channelId']
    except Exception as e:
        print(f"Chyba při získávání ID kanálu pro {channel_handle}: {e}")

    return None

def get_channel_videos(channel_id, max_results=10):
    """
    Získá seznam videí z kanálu
    """
    if not channel_id:
        return []

    url = f"{BASE_URL}/search?part=snippet&channelId={channel_id}&maxResults={max_results}&order=date&type=video&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        videos = []
        if 'items' in data:
            for item in data['items']:
                video_id = item['id']['videoId']
                published_at = item['snippet']['publishedAt']

                # Kontrola, zda je video dostatečně nové
                published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                now = datetime.now().astimezone()
                age_hours = (now - published_date).total_seconds() / 3600

                if age_hours <= NEW_VIDEO_MAX_AGE_HOURS:
                    videos.append({
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails']['high']['url'],
                        'published_at': published_at,
                        'channel_title': item['snippet']['channelTitle']
                    })

        return videos
    except Exception as e:
        print(f"Chyba při získávání videí z kanálu {channel_id}: {e}")
        return []

def get_live_streams(channel_id, max_results=5):
    """
    Získá seznam aktivních nebo naplánovaných live streamů z kanálu
    """
    if not channel_id:
        return []

    url = f"{BASE_URL}/search?part=snippet&channelId={channel_id}&maxResults={max_results}&eventType=live&type=video&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        live_streams = []
        if 'items' in data:
            for item in data['items']:
                video_id = item['id']['videoId']
                # Získáme detailní informace o live streamu
                stream_details = get_video_details(video_id)
                if stream_details:
                    live_streams.append(stream_details)

        # Získáme také naplánované streamy
        url = f"{BASE_URL}/search?part=snippet&channelId={channel_id}&maxResults={max_results}&eventType=upcoming&type=video&key={YOUTUBE_API_KEY}"
        response = requests.get(url)
        data = response.json()

        if 'items' in data:
            for item in data['items']:
                video_id = item['id']['videoId']
                # Získáme detailní informace o naplánovaném streamu
                stream_details = get_video_details(video_id)
                if stream_details:
                    live_streams.append(stream_details)

        return live_streams
    except Exception as e:
        print(f"Chyba při získávání live streamů z kanálu {channel_id}: {e}")
        return []

def get_video_details(video_id):
    """
    Získá detailní informace o videu
    """
    if not video_id:
        return None

    url = f"{BASE_URL}/videos?part=snippet,contentDetails,statistics,liveStreamingDetails&id={video_id}&key={YOUTUBE_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            item = data['items'][0]
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            live_details = item.get('liveStreamingDetails', {})

            # Zpracování délky videa
            duration = "0:00"
            if 'duration' in content_details:
                # Formát ISO 8601 duration: PT#H#M#S
                iso_duration = content_details['duration']
                hours = 0
                minutes = 0
                seconds = 0

                # Extrakce hodin, minut a sekund pomocí regulárních výrazů
                hour_match = re.search(r'(\d+)H', iso_duration)
                if hour_match:
                    hours = int(hour_match.group(1))

                minute_match = re.search(r'(\d+)M', iso_duration)
                if minute_match:
                    minutes = int(minute_match.group(1))

                second_match = re.search(r'(\d+)S', iso_duration)
                if second_match:
                    seconds = int(second_match.group(1))

                # Výpočet celkového počtu sekund
                total_seconds = hours * 3600 + minutes * 60 + seconds

                # Formátování výstupu
                if hours > 0:
                    duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    duration = f"{minutes}:{seconds:02d}"

            # Kontrola, zda je video live stream
            is_live = False
            scheduled_start_time = None
            actual_start_time = None

            if 'liveBroadcastContent' in snippet and snippet['liveBroadcastContent'] != 'none':
                is_live = snippet['liveBroadcastContent'] == 'live'

                if 'scheduledStartTime' in live_details:
                    scheduled_start_time = live_details['scheduledStartTime']

                if 'actualStartTime' in live_details:
                    actual_start_time = live_details['actualStartTime']

            return {
                'id': video_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'thumbnail': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url'],
                'published_at': snippet['publishedAt'],
                'channel_title': snippet['channelTitle'],
                'duration': duration,
                'views': statistics.get('viewCount', '0'),
                'likes': statistics.get('likeCount', '0'),
                'comments': statistics.get('commentCount', '0'),
                'is_live': is_live,
                'scheduled_start_time': scheduled_start_time,
                'actual_start_time': actual_start_time
            }

        return None
    except Exception as e:
        print(f"Chyba při získávání detailů videa {video_id}: {e}")
        return None

def update_video_stats(video_id):
    """
    Aktualizuje statistiky videa v databázi
    """
    if not video_id:
        return False

    video_details = get_video_details(video_id)
    if video_details:
        db.save_video(video_details)
        return True

    return False
