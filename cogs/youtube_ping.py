import discord
import asyncio
import os
import json
from datetime import datetime, time, timedelta
from discord.ext import commands, tasks
from utils import config, db, youtube

# Načtení konfigurace
GUILD_ID = config.get_int('GUILD_ID')
YOUTUBE_CHANNELS = config.get('YOUTUBE_CHANNEL_ID', '@davidstrejc').split(',')
YOUTUBE_NOTIFICATION_CHANNEL_ID = config.get_int('YOUTUBE_NOTIFICATION_CHANNEL_ID')
YOUTUBE_PING_ROLE_ID = config.get_int('YOUTUBE_PING_ROLE_ID')
CHECK_INTERVAL_SECONDS = config.get_int('CHECK_INTERVAL_SECONDS', 5)

class YoutubePing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_check = {}  # Poslední kontrola pro každý kanál
        self.channel_ids = {}  # Mapování handle na ID kanálu
        self.announced_videos = set()  # Set pro sledování oznámených videí
        self.check_videos.start()
        self.update_stats.start()
        
        # Inicializace posledních kontrol pro každý kanál
        for channel in YOUTUBE_CHANNELS:
            self.last_check[channel.strip()] = datetime.now()
    
    def cog_unload(self):
        self.check_videos.cancel()
        self.update_stats.cancel()
    
    @tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
    async def check_videos(self):
        """Kontroluje nová videa na YouTube kanálech"""
        if not YOUTUBE_NOTIFICATION_CHANNEL_ID:
            return
        
        channel = self.bot.get_channel(YOUTUBE_NOTIFICATION_CHANNEL_ID)
        if not channel:
            print(f"Kanál s ID {YOUTUBE_NOTIFICATION_CHANNEL_ID} nebyl nalezen")
            return
        
        for yt_channel in YOUTUBE_CHANNELS:
            yt_channel = yt_channel.strip()
            if not yt_channel:
                continue
            
            # Získání ID kanálu
            if yt_channel not in self.channel_ids:
                channel_id = youtube.get_channel_id(yt_channel)
                if not channel_id:
                    print(f"Nepodařilo se získat ID kanálu pro {yt_channel}")
                    continue
                self.channel_ids[yt_channel] = channel_id
            else:
                channel_id = self.channel_ids[yt_channel]
            
            # Kontrola nových videí
            try:
                # Získání videí
                videos = youtube.get_channel_videos(channel_id, max_results=5)
                
                # Kontrola live streamů
                live_streams = youtube.get_live_streams(channel_id)
                
                # Přidání live streamů do seznamu videí
                for stream in live_streams:
                    if stream['id'] not in [v['id'] for v in videos]:
                        videos.append(stream)
                
                # Kontrola nových videí
                for video in videos:
                    video_id = video['id']
                    
                    # Kontrola, zda video již bylo oznámeno
                    if db.is_video_announced(video_id) or video_id in self.announced_videos:
                        continue
                    
                    # Získání detailů videa
                    video_details = youtube.get_video_details(video_id)
                    if not video_details:
                        continue
                    
                    # Oznámení nového videa
                    await self.announce_video(channel, video_details, yt_channel)
                    
                    # Přidání videa do setu oznámených videí
                    self.announced_videos.add(video_id)
            
            except Exception as e:
                print(f"Chyba při kontrole videí pro kanál {yt_channel}: {e}")
    
    @check_videos.before_loop
    async def before_check_videos(self):
        await self.bot.wait_until_ready()
    
    @tasks.loop(minutes=30)
    async def update_stats(self):
        """Aktualizuje statistiky posledních 3 videí každých 30 minut"""
        if not YOUTUBE_NOTIFICATION_CHANNEL_ID:
            return
        
        channel = self.bot.get_channel(YOUTUBE_NOTIFICATION_CHANNEL_ID)
        if not channel:
            print(f"Kanál s ID {YOUTUBE_NOTIFICATION_CHANNEL_ID} nebyl nalezen")
            return
        
        # Získání posledních 3 oznámených videí
        announced_videos = db.get_announced_videos()
        if not announced_videos:
            return
        
        # Omezení na poslední 3 videa
        videos_to_update = announced_videos[:3]
        
        for video in videos_to_update:
            try:
                # Aktualizace statistik videa
                video_id = video.get('video_id')
                if not video_id:
                    continue
                
                # Aktualizace statistik v databázi
                youtube.update_video_stats(video_id)
                
                # Aktualizace embedu
                message_id = video.get('message_id')
                if not message_id:
                    continue
                
                try:
                    # Získání zprávy
                    message = await channel.fetch_message(int(message_id))
                    if not message:
                        continue
                    
                    # Aktualizace embedu
                    updated_video = db.get_video(video_id)
                    if not updated_video:
                        continue
                    
                    embed = self.create_video_embed(updated_video)
                    await message.edit(embed=embed)
                    
                    print(f"Aktualizovány statistiky pro video {video_id}")
                except discord.NotFound:
                    print(f"Zpráva s ID {message_id} nebyla nalezena")
                except discord.Forbidden:
                    print(f"Bot nemá oprávnění upravit zprávu s ID {message_id}")
                except Exception as e:
                    print(f"Chyba při aktualizaci embedu pro video {video_id}: {e}")
            
            except Exception as e:
                print(f"Chyba při aktualizaci statistik pro video {video.get('video_id')}: {e}")
    
    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()
        
        # Počkáme, až bude celá nebo půl hodiny
        now = datetime.now()
        minutes_to_wait = 30 - (now.minute % 30)
        seconds_to_wait = minutes_to_wait * 60 - now.second
        
        if seconds_to_wait > 0:
            print(f"Čekání {seconds_to_wait} sekund do další celé/půl hodiny pro aktualizaci statistik")
            await asyncio.sleep(seconds_to_wait)
    
    async def announce_video(self, channel, video, yt_channel):
        """Oznámí nové video v kanálu"""
        try:
            # Vytvoření embedu
            embed = self.create_video_embed(video)
            
            # Přidání videa do databáze
            db.save_video(video)
            
            # Ping role
            ping_text = ""
            if YOUTUBE_PING_ROLE_ID:
                ping_text = f"<@&{YOUTUBE_PING_ROLE_ID}> "
            
            # Odeslání zprávy s embedem
            message = await channel.send(f"{ping_text}Nové video na kanálu **{yt_channel}**!", embed=embed)
            
            # Aktualizace ID zprávy v databázi
            db.update_message_ids(video['id'], message.id, channel.id)
            
            print(f"Oznámeno nové video: {video['title']}")
            
            return True
        except Exception as e:
            print(f"Chyba při oznamování videa: {e}")
            return False
    
    def create_video_embed(self, video):
        """Vytvoří embed pro video"""
        # Základní informace
        video_id = video.get('video_id')
        title = video.get('title')
        description = video.get('description', '')
        thumbnail_url = video.get('thumbnail_url')
        published_at = video.get('published_at')
        channel_title = video.get('channel_title')
        duration = video.get('duration', '0:00')
        views = int(video.get('views', 0))
        likes = int(video.get('likes', 0))
        comments = int(video.get('comments', 0))
        is_live = video.get('is_live', False)
        
        # Formátování data publikace
        published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        published_str = f"<t:{int(published_date.timestamp())}:F>"
        
        # Vytvoření embedu
        embed = discord.Embed(
            title=title,
            url=f"https://www.youtube.com/watch?v={video_id}",
            description=description[:200] + "..." if len(description) > 200 else description,
            color=discord.Color.red()
        )
        
        # Přidání obrázku
        embed.set_thumbnail(url=thumbnail_url)
        
        # Přidání informací o videu
        if is_live:
            embed.add_field(name="🔴 ŽIVĚ", value="Stream právě probíhá!", inline=False)
        
        embed.add_field(name="Kanál", value=channel_title, inline=True)
        embed.add_field(name="Publikováno", value=published_str, inline=True)
        
        if not is_live:
            embed.add_field(name="Délka", value=duration, inline=True)
        
        # Statistiky
        stats = []
        if views > 0:
            stats.append(f"👁️ {views:,}".replace(',', ' '))
        if likes > 0:
            stats.append(f"👍 {likes:,}".replace(',', ' '))
        if comments > 0:
            stats.append(f"💬 {comments:,}".replace(',', ' '))
        
        if stats:
            embed.add_field(name="Statistiky", value=" | ".join(stats), inline=False)
        
        # Přidání časového razítka
        embed.set_footer(text=f"Poslední aktualizace: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        return embed

async def setup(bot):
    await bot.add_cog(YoutubePing(bot))
