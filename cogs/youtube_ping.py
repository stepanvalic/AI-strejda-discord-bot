import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import datetime
from datetime import timedelta
from utils import db, config

YOUTUBE_API_KEY = config.get('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL = config.get('YOUTUBE_CHANNEL_ID')

IS_USERNAME = YOUTUBE_CHANNEL.startswith('@')
YOUTUBE_USERNAME = YOUTUBE_CHANNEL if IS_USERNAME else None
YOUTUBE_CHANNEL_ID = None if IS_USERNAME else YOUTUBE_CHANNEL

YOUTUBE_NOTIFICATION_CHANNEL_ID = config.get_int('YOUTUBE_NOTIFICATION_CHANNEL_ID')
YOUTUBE_PING_ROLE_ID = config.get_int('YOUTUBE_PING_ROLE_ID', 0)

CHECK_INTERVAL_SECONDS = config.get_int('CHECK_INTERVAL_SECONDS', 15)

# Maximum age of a video to be considered "new" when the bot starts (in hours)
# This helps catch videos published while the bot was offline
NEW_VIDEO_MAX_AGE_HOURS = config.get_int('NEW_VIDEO_MAX_AGE_HOURS', 24)

# Nastavení pro odložené notifikace - nyní vždy vypnuto
NOTIFICATION_DELAY_ENABLED = False  # Natvrdo nastaveno na False, aby se notifikace vždy odesílaly okamžitě
NOTIFICATION_DELAY_START_HOUR = 0
NOTIFICATION_DELAY_END_HOUR = 0
NOTIFICATION_DELAY_UNTIL_HOUR = 0

UPDATE_INTERVAL_SECONDS = 30 * 60

class YouTubePing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_video_id = None
        self.initialized = False
        self.session = None

        db.ensure_db_exists()

        self.check_uploads.start()
        self.update_embeds.start()

    def cog_unload(self):
        self.check_uploads.cancel()
        self.update_embeds.cancel()
        
        # Close aiohttp session if it exists
        if self.session and not self.session.closed:
            asyncio.create_task(self._close_session())

    async def _close_session(self):
        """Safely close the aiohttp session"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                # Wait a bit for the underlying connections to close
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error closing aiohttp session: {e}")

    async def _get_session(self):
        """Get or create aiohttp session with proper timeout settings"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                ssl=False  # Disable SSL verification to avoid SSL timeout issues
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        return self.session

    async def get_channel_id_from_username(self, username):
        if username.startswith('@'):
            username = username[1:]

        url = f"https://www.googleapis.com/youtube/v3/channels?key={YOUTUBE_API_KEY}&forUsername={username}&part=id"

        session = await self._get_session()
        try:
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
        except Exception as e:
            print(f"Error getting channel ID from username: {e}")
        return None

    async def get_latest_video(self):
        channel_id = YOUTUBE_CHANNEL_ID

        if IS_USERNAME and not channel_id:
            channel_id = await self.get_channel_id_from_username(YOUTUBE_USERNAME)
            if not channel_id:
                print(f"Could not find channel ID for username {YOUTUBE_USERNAME}")
                return None

        # Hledáme videa i live streamy (type=video,live)
        search_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=5&type=video"

        session = await self._get_session()
        try:
            async with session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()

                    if not data.get('items'):
                        print(f"No videos found for channel ID {channel_id}")
                        return None

                    # Procházíme výsledky a hledáme nejnovější video nebo live stream
                    for item in data['items']:
                        video_id = item['id'].get('videoId')
                        if not video_id:
                            continue

                        video_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&id={video_id}&part=snippet,contentDetails,statistics,liveStreamingDetails"

                        async with session.get(video_url) as video_response:
                            if video_response.status == 200:
                                video_data = await video_response.json()

                                if not video_data.get('items'):
                                    continue

                                video_info = video_data['items'][0]
                                snippet = video_info['snippet']
                                content_details = video_info['contentDetails']
                                statistics = video_info['statistics']

                                # Zjistíme, zda je to live stream
                                is_live = False
                                scheduled_start_time = None
                                actual_start_time = None

                                if 'liveStreamingDetails' in video_info:
                                    live_details = video_info['liveStreamingDetails']

                                    # Kontrola, zda je to aktivní live stream
                                    if live_details.get('actualEndTime') is None and (
                                        live_details.get('actualStartTime') is not None or
                                        live_details.get('scheduledStartTime') is not None
                                    ):
                                        is_live = True
                                        scheduled_start_time = live_details.get('scheduledStartTime')
                                        actual_start_time = live_details.get('actualStartTime')

                                # Získáme délku videa (pro live streamy to může být 0)
                                duration_iso = content_details.get('duration', 'PT0S')
                                duration = self.parse_duration(duration_iso)

                                # Vytvoříme objekt s informacemi o videu/streamu
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
                                    'channel_title': snippet['channelTitle'],
                                    'is_live': is_live,
                                    'scheduled_start_time': scheduled_start_time,
                                    'actual_start_time': actual_start_time
                                }
        except Exception as e:
            print(f"Error getting latest video: {e}")
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

    def is_video_recent(self, published_at):
        """Check if a video was published recently (within NEW_VIDEO_MAX_AGE_HOURS)"""
        try:
            # Parse the published_at string to a datetime object
            published_time = datetime.datetime.fromisoformat(published_at.replace('Z', '+00:00'))

            # Calculate the time difference
            now = datetime.datetime.now(datetime.timezone.utc)
            time_diff = now - published_time

            # Check if the video is within the max age
            return time_diff <= timedelta(hours=NEW_VIDEO_MAX_AGE_HOURS)
        except Exception as e:
            print(f"Error checking if video is recent: {str(e)}")
            # If there's an error, assume it's not recent to avoid spam
            return False

    @tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
    async def check_uploads(self):
        if not YOUTUBE_API_KEY:
            print("YouTube API key is missing")
            return

        # Kontrola nových videí
        video = await self.get_latest_video()

        if not video:
            return

        # Save the video to the database
        db.save_video(video)

        # Check if the video has already been announced
        if db.is_video_announced(video['id']):
            # Update the last_video_id if needed
            if self.last_video_id != video['id']:
                self.last_video_id = video['id']
            return

        # Simplified initialization - just set the last video ID on first run
        if not self.initialized:
            self.initialized = True
            announced_videos = db.get_announced_videos()

            if announced_videos:
                # We have announced videos before, use the latest one as reference
                self.last_video_id = announced_videos[0]['video_id']
                print(f"Initialized with last announced video: {self.last_video_id}")
            else:
                # No videos announced yet, set current video as reference without announcing
                self.last_video_id = video['id']
                print(f"First run - setting reference video: {video['id']}")
            return

        # If last_video_id is still None (shouldn't happen, but just in case)
        if self.last_video_id is None:
            self.last_video_id = video['id']
            print(f"Setting last_video_id to current video: {video['id']}")
            return

        # Normal operation - announce if it's a new video
        if video['id'] != self.last_video_id:
            print(f"New video detected: {video['title']}")
            self.last_video_id = video['id']
            await self.send_notification(video)

    @check_uploads.before_loop
    async def before_check_uploads(self):
        await self.bot.wait_until_ready()

    async def send_notification(self, video):
        # Odstraněna logika pro odložené notifikace - všechny notifikace budou odeslány okamžitě
        # Přidáme pouze log pro informaci
        print(f"[YouTube] Odesílám okamžitou notifikaci pro video '{video['title']}'")

        channel = self.bot.get_channel(YOUTUBE_NOTIFICATION_CHANNEL_ID)

        if not channel:
            return

        embed = await self.create_video_embed(video)

        channel_url = f"https://www.youtube.com/{YOUTUBE_CHANNEL}" if IS_USERNAME else f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL}"

        # Upravíme název podle typu obsahu
        if video.get('is_live', False):
            if video.get('actual_start_time'):
                author_name = f"🔴 {video['channel_title']} právě vysílá živě!"
            else:
                author_name = f"🔴 {video['channel_title']} naplánoval živé vysílání!"
        else:
            author_name = f"Nové video od {video['channel_title']}!"

        embed.set_author(
            name=author_name,
            icon_url="https://s.ytimg.com/yts/img/favicon_144-vfliLAfaB.png",
            url=channel_url
        )

        # Přidáme různý obsah zprávy podle typu
        if video.get('is_live', False):
            if video.get('actual_start_time'):
                # Pro živé vysílání použijeme roli nebo @everyone
                if YOUTUBE_PING_ROLE_ID:
                    content = f"<@&{YOUTUBE_PING_ROLE_ID}> {video['channel_title']} právě vysílá živě! Připojte se ke streamu!"
                else:
                    content = f"@everyone {video['channel_title']} právě vysílá živě! Připojte se ke streamu!"
            else:
                # Pro naplánované streamy nepoužíváme @everyone ani roli
                scheduled_time = None
                if video.get('scheduled_start_time'):
                    scheduled_time = datetime.datetime.fromisoformat(video['scheduled_start_time'].replace('Z', '+00:00'))
                    # Převedeme na lokální čas
                    local_time = scheduled_time.astimezone()
                    time_str = local_time.strftime("%d.%m.%Y v %H:%M")
                    content = f"{video['channel_title']} naplánoval živé vysílání na {time_str}!"
                else:
                    content = f"{video['channel_title']} naplánoval živé vysílání!"
        else:
            # Pro běžná videa použijeme roli nebo @everyone
            if YOUTUBE_PING_ROLE_ID:
                content = f"<@&{YOUTUBE_PING_ROLE_ID}> Nové video od {video['channel_title']}!"
            else:
                content = f"@everyone Nové video od {video['channel_title']}!"

        message = await channel.send(
            content=content,
            embed=embed
        )

        db.update_message_ids(video['id'], str(message.id), str(channel.id))

    @tasks.loop(seconds=UPDATE_INTERVAL_SECONDS)
    async def update_embeds(self):

        announced_videos = db.get_announced_videos()

        if not announced_videos:
            return

        videos_to_update = announced_videos[:5]

        for video_data in videos_to_update:
            if not video_data.get('message_id') or not video_data.get('channel_message_id'):
                continue

            try:
                updated_video = await self.get_video_details(video_data['video_id'])

                if not updated_video:
                    continue

                channel_id = int(video_data['channel_message_id'])
                message_id = int(video_data['message_id'])

                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue

                try:
                    message = await channel.fetch_message(message_id)
                except discord.NotFound:
                    continue

                embed = await self.create_video_embed(updated_video)

                await message.edit(embed=embed)

                db.save_video(updated_video, str(message_id), str(channel_id))

            except Exception as e:
                print(f"Error updating embed for video {video_data['video_id']}: {str(e)}")

    @update_embeds.before_loop
    async def before_update_embeds(self):
        await self.bot.wait_until_ready()

    async def get_video_details(self, video_id):
        if not YOUTUBE_API_KEY:
            return None

        video_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&id={video_id}&part=snippet,contentDetails,statistics,liveStreamingDetails"

        session = await self._get_session()
        try:
            async with session.get(video_url) as response:
                if response.status == 200:
                    data = await response.json()

                    if not data.get('items') or not data['items']:
                        return None

                    video_info = data['items'][0]
                    snippet = video_info['snippet']
                    content_details = video_info['contentDetails']
                    statistics = video_info['statistics']

                    # Zjistíme, zda je to live stream
                    is_live = False
                    scheduled_start_time = None
                    actual_start_time = None

                    if 'liveStreamingDetails' in video_info:
                        live_details = video_info['liveStreamingDetails']

                        # Kontrola, zda je to aktivní live stream
                        if live_details.get('actualEndTime') is None and (
                            live_details.get('actualStartTime') is not None or
                            live_details.get('scheduledStartTime') is not None
                        ):
                            is_live = True
                            scheduled_start_time = live_details.get('scheduledStartTime')
                            actual_start_time = live_details.get('actualStartTime')

                    duration_iso = content_details.get('duration', 'PT0S')
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
                        'channel_title': snippet['channelTitle'],
                        'is_live': is_live,
                        'scheduled_start_time': scheduled_start_time,
                        'actual_start_time': actual_start_time
                    }
        except Exception as e:
            print(f"Error getting video details: {e}")
        return None

    async def create_video_embed(self, video):
        short_description = video['description'][:200]
        if len(video['description']) > 200:
            last_space = short_description.rfind(' ')
            if last_space > 150:
                short_description = short_description[:last_space] + "..."
            else:
                short_description += "..."

        # Určíme barvu podle typu obsahu (červená pro videa, purpurová pro live streamy)
        color = discord.Color.purple() if video.get('is_live', False) else discord.Color.red()

        embed = discord.Embed(
            title=video['title'],
            description=short_description,
            color=color,
            url=f"https://www.youtube.com/watch?v={video['id']}"
        )

        channel_url = f"https://www.youtube.com/{YOUTUBE_CHANNEL}" if IS_USERNAME else f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL}"

        # Upravíme název podle typu obsahu
        if video.get('is_live', False):
            author_name = f"Live stream od {video['channel_title']}"
        else:
            author_name = f"Video od {video['channel_title']}"

        embed.set_author(
            name=author_name,
            icon_url="https://s.ytimg.com/yts/img/favicon_144-vfliLAfaB.png",
            url=channel_url
        )

        embed.set_image(url=video['thumbnail'])

        # Přidáme různá pole podle typu obsahu
        if video.get('is_live', False):
            embed.add_field(name="Typ", value="`🔴 ŽIVĚ`", inline=True)
            embed.add_field(name="Zhlédnutí", value=f"`{int(video['views']):,}`".replace(',', ' '), inline=True)

            # Pokud máme informaci o začátku streamu, zobrazíme ji
            if video.get('actual_start_time'):
                start_time = datetime.datetime.fromisoformat(video['actual_start_time'].replace('Z', '+00:00'))
                time_diff = datetime.datetime.now(datetime.timezone.utc) - start_time
                hours = int(time_diff.total_seconds() // 3600)
                minutes = int((time_diff.total_seconds() % 3600) // 60)

                if hours > 0:
                    duration_str = f"{hours}h {minutes}m"
                else:
                    duration_str = f"{minutes}m"

                embed.add_field(name="Trvání streamu", value=f"`{duration_str}`", inline=True)
        else:
            embed.add_field(name="Délka videa", value=f"`{video['duration']}`", inline=True)
            embed.add_field(name="Zhlédnutí", value=f"`{int(video['views']):,}`".replace(',', ' '), inline=True)
            embed.add_field(name="Lajky", value=f"`{int(video['likes']):,}`".replace(',', ' '), inline=True)

        # Nastavíme patičku podle typu obsahu
        published_time = datetime.datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))

        if video.get('is_live', False):
            if video.get('actual_start_time'):
                embed.set_footer(text=f"Stream ID: {video['id']} • Stream začal")
                embed.timestamp = datetime.datetime.fromisoformat(video['actual_start_time'].replace('Z', '+00:00'))
            else:
                embed.set_footer(text=f"Stream ID: {video['id']} • Naplánováno na")
                if video.get('scheduled_start_time'):
                    embed.timestamp = datetime.datetime.fromisoformat(video['scheduled_start_time'].replace('Z', '+00:00'))
                else:
                    embed.timestamp = published_time
        else:
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

    @commands.command(name="ytlastvideosend")
    @commands.has_permissions(administrator=True)
    async def send_last_video(self, ctx):
        """Pošle poslední video do nastaveného kanálu (admin only)"""
        if not YOUTUBE_NOTIFICATION_CHANNEL_ID:
            await ctx.send("Není nastaven kanál pro oznámení YouTube videí v .env souboru.", ephemeral=True)
            return

        await ctx.send("Zjišťuji poslední video a posílám ho do nastaveného kanálu...", ephemeral=True)

        # Get the latest video
        video = await self.get_latest_video()

        if not video:
            await ctx.send("Nepodařilo se získat informace o nejnovějším videu.", ephemeral=True)
            return

        # Save the video to the database
        db.save_video(video)

        # Send the notification
        await self.send_notification(video)

        # Update the last video ID
        self.last_video_id = video['id']

        await ctx.send(f"Poslední video '{video['title']}' bylo odesláno do kanálu.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(YouTubePing(bot))
