import discord
from discord.ext import commands, tasks
import os
import json
import aiohttp
import datetime
import re
from dotenv import load_dotenv
from utils import db

load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL = os.getenv('YOUTUBE_CHANNEL_ID')

IS_USERNAME = YOUTUBE_CHANNEL.startswith('@')
YOUTUBE_USERNAME = YOUTUBE_CHANNEL if IS_USERNAME else None
YOUTUBE_CHANNEL_ID = None if IS_USERNAME else YOUTUBE_CHANNEL

try:
    YOUTUBE_NOTIFICATION_CHANNEL_ID = int(os.getenv('YOUTUBE_NOTIFICATION_CHANNEL_ID', 0))
except ValueError:
    YOUTUBE_NOTIFICATION_CHANNEL_ID = 0
    print("Warning: Invalid YOUTUBE_NOTIFICATION_CHANNEL_ID in .env file")

try:
    CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', 30))
except ValueError:
    CHECK_INTERVAL_SECONDS = 30
    print("Warning: Invalid CHECK_INTERVAL_SECONDS in .env file")

UPDATE_INTERVAL_SECONDS = 5 * 60

class YouTubePing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_video_id = None

        db.ensure_db_exists()

        self.check_uploads.start()
        self.update_embeds.start()

    def cog_unload(self):
        self.check_uploads.cancel()
        self.update_embeds.cancel()

    async def get_channel_id_from_username(self, username):
        if username.startswith('@'):
            username = username[1:]

        url = f"https://www.googleapis.com/youtube/v3/channels?key={YOUTUBE_API_KEY}&forUsername={username}&part=id"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get('items') and len(data['items']) > 0:
                        return data['items'][0]['id']
                    else:
                        search_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&q={username}&type=channel&part=snippet"

                        async with session.get(search_url) as search_response:
                            if search_response.status == 200:
                                search_data = await search_response.json()

                                if search_data.get('items') and len(search_data['items']) > 0:
                                    for item in search_data['items']:
                                        channel_title = item['snippet']['channelTitle']
                                        if channel_title.lower() == username.lower() or f"@{username.lower()}" in channel_title.lower():
                                            return item['snippet']['channelId']

                                    return search_data['items'][0]['snippet']['channelId']
                return None

    async def get_latest_video(self):
        channel_id = YOUTUBE_CHANNEL_ID

        if IS_USERNAME and not channel_id:
            channel_id = await self.get_channel_id_from_username(YOUTUBE_USERNAME)
            if not channel_id:
                print(f"Could not find channel ID for username {YOUTUBE_USERNAME}")
                return None

        search_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=1&type=video"

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()

                    if not data.get('items'):
                        print(f"No videos found for channel ID {channel_id}")
                        return None

                    video_id = data['items'][0]['id'].get('videoId')
                    if not video_id:
                        return None

                    video_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&id={video_id}&part=snippet,contentDetails,statistics"

                    async with session.get(video_url) as video_response:
                        if video_response.status == 200:
                            video_data = await video_response.json()

                            if not video_data.get('items'):
                                return None

                            video_info = video_data['items'][0]
                            snippet = video_info['snippet']
                            content_details = video_info['contentDetails']
                            statistics = video_info['statistics']

                            duration_iso = content_details['duration']
                            duration = self.parse_duration(duration_iso)

                            return {
                                'id': video_id,
                                'title': snippet['title'],
                                'description': snippet['description'],
                                'thumbnail': snippet['thumbnails']['maxres']['url'] if 'maxres' in snippet['thumbnails'] else snippet['thumbnails']['high']['url'],
                                'published_at': snippet['publishedAt'],
                                'duration': duration,
                                'views': statistics.get('viewCount', '0'),
                                'likes': statistics.get('likeCount', '0'),
                                'comments': statistics.get('commentCount', '0'),
                                'channel_title': snippet['channelTitle']
                            }
                return None

    def parse_duration(self, duration_iso):
        duration = duration_iso[2:]
        hours = 0
        minutes = 0
        seconds = 0

        if 'H' in duration:
            hours_str, duration = duration.split('H')
            hours = int(hours_str)

        if 'M' in duration:
            minutes_str, duration = duration.split('M')
            minutes = int(minutes_str)

        if 'S' in duration:
            seconds_str = duration.split('S')[0]
            seconds = int(seconds_str)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    @tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
    async def check_uploads(self):
        if not YOUTUBE_API_KEY:
            print("YouTube API key is missing")
            return

        print(f"Checking for new videos on channel {YOUTUBE_CHANNEL}...")

        video = await self.get_latest_video()

        if not video:
            print("No videos found or error occurred")
            return

        print(f"Latest video found: {video['title']} (ID: {video['id']})")

        db.save_video(video)

        if db.is_video_announced(video['id']):
            print(f"Video {video['id']} was already announced")
            return

        if self.last_video_id is None:
            announced_videos = db.get_announced_videos()

            if announced_videos:
                self.last_video_id = announced_videos[0]['video_id']
                print(f"First run, setting last video ID to {self.last_video_id} from database")
            else:
                self.last_video_id = video['id']
                print(f"First run, setting last video ID to {video['id']}")
            return

        if video['id'] != self.last_video_id:
            print(f"New video detected! Old ID: {self.last_video_id}, New ID: {video['id']}")
            self.last_video_id = video['id']
            await self.send_notification(video)
        else:
            print(f"No new videos (last video ID: {self.last_video_id})")

    async def send_notification(self, video):
        channel = self.bot.get_channel(YOUTUBE_NOTIFICATION_CHANNEL_ID)

        if not channel:
            print(f"YouTube notification channel with ID {YOUTUBE_NOTIFICATION_CHANNEL_ID} not found!")
            return

        embed = await self.create_video_embed(video)

        channel_url = f"https://www.youtube.com/{YOUTUBE_CHANNEL}" if IS_USERNAME else f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL}"

        embed.set_author(
            name=f"Nové video od {video['channel_title']}!",
            icon_url="https://s.ytimg.com/yts/img/favicon_144-vfliLAfaB.png",
            url=channel_url
        )

        message = await channel.send(
            content=f"@everyone",
            embed=embed
        )

        db.update_message_ids(video['id'], str(message.id), str(channel.id))
        print(f"Notification sent for video {video['id']} with message ID {message.id}")

    @check_uploads.before_loop
    async def before_check_uploads(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=UPDATE_INTERVAL_SECONDS)
    async def update_embeds(self):
        print("Updating previous video embeds...")

        announced_videos = db.get_announced_videos()

        if not announced_videos:
            print("No announced videos found in database")
            return

        videos_to_update = announced_videos[:5]

        for video_data in videos_to_update:
            if not video_data.get('message_id') or not video_data.get('channel_message_id'):
                continue

            try:
                updated_video = await self.get_video_details(video_data['video_id'])

                if not updated_video:
                    print(f"Could not get updated information for video {video_data['video_id']}")
                    continue

                channel_id = int(video_data['channel_message_id'])
                message_id = int(video_data['message_id'])

                channel = self.bot.get_channel(channel_id)
                if not channel:
                    print(f"Could not find channel with ID {channel_id}")
                    continue

                try:
                    message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    print(f"Could not find message with ID {message_id} in channel {channel_id}")
                    continue

                embed = await self.create_video_embed(updated_video)

                await message.edit(embed=embed)

                db.save_video(updated_video, str(message_id), str(channel_id))

                print(f"Updated embed for video {updated_video['id']} (views: {updated_video['views']}, likes: {updated_video['likes']})")

            except Exception as e:
                print(f"Error updating embed for video {video_data['video_id']}: {str(e)}")

    @update_embeds.before_loop
    async def before_update_embeds(self):
        await self.bot.wait_until_ready()

    async def get_video_details(self, video_id):
        if not YOUTUBE_API_KEY:
            return None

        video_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&id={video_id}&part=snippet,contentDetails,statistics"

        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status == 200:
                    data = await response.json()

                    if not data.get('items') or not data['items']:
                        return None

                    video_info = data['items'][0]
                    snippet = video_info['snippet']
                    content_details = video_info['contentDetails']
                    statistics = video_info['statistics']

                    duration_iso = content_details['duration']
                    duration = self.parse_duration(duration_iso)

                    return {
                        'id': video_id,
                        'title': snippet['title'],
                        'description': snippet['description'],
                        'thumbnail': snippet['thumbnails']['maxres']['url'] if 'maxres' in snippet['thumbnails'] else snippet['thumbnails']['high']['url'],
                        'published_at': snippet['publishedAt'],
                        'duration': duration,
                        'views': statistics.get('viewCount', '0'),
                        'likes': statistics.get('likeCount', '0'),
                        'comments': statistics.get('commentCount', '0'),
                        'channel_title': snippet['channelTitle']
                    }
                return None

    async def create_video_embed(self, video):
        short_description = video['description'][:200]
        if len(video['description']) > 200:
            last_space = short_description.rfind(' ')
            if last_space > 150:
                short_description = short_description[:last_space] + "..."
            else:
                short_description += "..."

        embed = discord.Embed(
            title=video['title'],
            description=short_description,
            color=discord.Color.red(),
            url=f"https://www.youtube.com/watch?v={video['id']}"
        )

        channel_url = f"https://www.youtube.com/{YOUTUBE_CHANNEL}" if IS_USERNAME else f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL}"

        embed.set_author(
            name=f"Video od {video['channel_title']}",
            icon_url="https://s.ytimg.com/yts/img/favicon_144-vfliLAfaB.png",
            url=channel_url
        )

        embed.set_image(url=video['thumbnail'])

        embed.add_field(name="Délka videa", value=f"`{video['duration']}`", inline=True)
        embed.add_field(name="Zhlédnutí", value=f"`{int(video['views']):,}`".replace(',', ' '), inline=True)
        embed.add_field(name="Lajky", value=f"`{int(video['likes']):,}`".replace(',', ' '), inline=True)

        published_time = datetime.datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
        embed.set_footer(text=f"Video ID: {video['id']} • Publikováno")
        embed.timestamp = published_time

        return embed

    @commands.command(name="checkyoutube")
    @commands.has_permissions(administrator=True)
    async def check_youtube(self, ctx):
        video = await self.get_latest_video()

        if video:
            await ctx.send(f"Nejnovější video: {video['title']} (ID: {video['id']})")
            self.last_video_id = video['id']

            db.save_video(video)
        else:
            await ctx.send("Nepodařilo se získat informace o nejnovějším videu.")

    @commands.command(name="updatevideos")
    @commands.has_permissions(administrator=True)
    async def update_videos(self, ctx):
        await ctx.send("Aktualizuji embedy pro všechna oznámená videa...")

        await self.update_embeds()

        await ctx.send("Aktualizace dokončena!")

async def setup(bot):
    await bot.add_cog(YouTubePing(bot))
