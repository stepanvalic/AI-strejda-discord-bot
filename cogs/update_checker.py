# import os
# import json
# import aiohttp
# import discord
# from discord.ext import commands, tasks
# from dotenv import load_dotenv
# from datetime import datetime
#
# load_dotenv()
#
# try:
#     UPDATE_CHECK_CHANNEL_ID = int(os.getenv('UPDATE_CHECK_CHANNEL_ID', 0))
# except ValueError:
#     UPDATE_CHECK_CHANNEL_ID = 0
#     print("Warning: Invalid UPDATE_CHECK_CHANNEL_ID in .env file")
#
# try:
#     UPDATE_CHECK_INTERVAL_HOURS = int(os.getenv('UPDATE_CHECK_INTERVAL_HOURS', 1))
# except ValueError:
#     UPDATE_CHECK_INTERVAL_HOURS = 1
#     print("Warning: Invalid UPDATE_CHECK_INTERVAL_HOURS in .env file")
#
# CURRENT_VERSION = os.getenv('CURRENT_VERSION', '0.01')
# GITHUB_REPO = "stepanvalic/AI-strejda-discord-bot"
# GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
# DB_PATH = "db/updates.json"
#
# class UpdateChecker(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#         self.ensure_db_exists()
#         self.check_for_updates.start()
#         self.bot.loop.create_task(self.send_startup_message())
#
#     async def send_startup_message(self):
#         await self.bot.wait_until_ready()
#
#         if UPDATE_CHECK_CHANNEL_ID == 0:
#             print("Update notification channel not set, skipping startup message")
#             return
#
#         channel = self.bot.get_channel(UPDATE_CHECK_CHANNEL_ID)
#         if not channel:
#             print(f"Could not find channel with ID {UPDATE_CHECK_CHANNEL_ID}")
#             return
#
#         embed = discord.Embed(
#             title="🤖 Bot byl spuštěn",
#             description=f"Bot byl právě spuštěn. Aktuální verze: v{CURRENT_VERSION}",
#             color=discord.Color.green(),
#             timestamp=datetime.now().astimezone()
#         )
#
#         embed.add_field(
#             name="Kontrola aktualizací",
#             value=f"Bot bude automaticky kontrolovat aktualizace každou hodinu.",
#             inline=False
#         )
#
#         embed.set_footer(text=f"GitHub: {GITHUB_REPO}")
#
#         await channel.send(embed=embed)
#         print("Sent bot startup message")
#
#     def cog_unload(self):
#         self.check_for_updates.cancel()
#
#     def ensure_db_exists(self):
#         os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
#
#         if not os.path.exists(DB_PATH):
#             with open(DB_PATH, 'w', encoding='utf-8') as f:
#                 json.dump({
#                     "last_check": None,
#                     "latest_version": CURRENT_VERSION,
#                     "last_notification": None
#                 }, f, ensure_ascii=False, indent=2)
#
#     def _load_db(self):
#         try:
#             with open(DB_PATH, 'r', encoding='utf-8') as f:
#                 return json.load(f)
#         except json.JSONDecodeError:
#             return {
#                 "last_check": None,
#                 "latest_version": CURRENT_VERSION,
#                 "last_notification": None
#             }
#
#     def _save_db(self, db_data):
#         with open(DB_PATH, 'w', encoding='utf-8') as f:
#             json.dump(db_data, f, ensure_ascii=False, indent=2)
#
#     def _update_last_check(self, version=None):
#         db = self._load_db()
#         db["last_check"] = datetime.now().isoformat()
#         if version:
#             db["latest_version"] = version
#         self._save_db(db)
#
#     def _update_last_notification(self, version):
#         db = self._load_db()
#         db["last_notification"] = datetime.now().isoformat()
#         db["latest_version"] = version
#         self._save_db(db)
#
#     def _get_latest_notified_version(self):
#         db = self._load_db()
#         return db.get("latest_version", CURRENT_VERSION)
#
#     @tasks.loop(hours=UPDATE_CHECK_INTERVAL_HOURS)
#     async def check_for_updates(self):
#         print(f"Checking for updates on GitHub repository {GITHUB_REPO}...")
#
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(GITHUB_API_URL) as response:
#                     if response.status != 200:
#                         print(f"Failed to check for updates: HTTP {response.status}")
#                         self._update_last_check()
#                         return
#
#                     data = await response.json()
#                     latest_version = data.get('tag_name', '').lstrip('v')
#
#                     if not latest_version:
#                         print("No version tag found in the latest release")
#                         self._update_last_check()
#                         return
#
#                     print(f"Current version: {CURRENT_VERSION}, Latest version: {latest_version}")
#
#                     # Always send a status message
#                     if latest_version != CURRENT_VERSION:
#                         # New version available
#                         await self.send_update_notification(latest_version, data, is_new=True)
#                         self._update_last_notification(latest_version)
#                     else:
#                         # Bot is up to date
#                         await self.send_update_notification(latest_version, data, is_new=False)
#                         print("Bot is up to date")
#
#                     self._update_last_check(latest_version)
#
#         except Exception as e:
#             print(f"Error checking for updates: {str(e)}")
#             self._update_last_check()
#
#     async def send_update_notification(self, version, release_data, is_new=True):
#         if UPDATE_CHECK_CHANNEL_ID == 0:
#             print("Update notification channel not set, skipping notification")
#             return
#
#         channel = self.bot.get_channel(UPDATE_CHECK_CHANNEL_ID)
#         if not channel:
#             print(f"Could not find channel with ID {UPDATE_CHECK_CHANNEL_ID}")
#             return
#
#         release_url = release_data.get('html_url', f"https://github.com/{GITHUB_REPO}/releases/tag/{version}")
#         release_notes = release_data.get('body', 'Žádné poznámky k vydání nejsou k dispozici.')
#
#         if is_new:
#             # New version available
#             embed = discord.Embed(
#                 title=f"🚀 Nová verze bota je k dispozici: v{version}",
#                 description="Je dostupná nová verze bota. Aktualizujte pro získání nejnovějších funkcí a oprav.",
#                 color=discord.Color.blue(),
#                 url=release_url,
#                 timestamp=datetime.now().astimezone()
#             )
#
#             embed.add_field(
#                 name="Aktuální verze",
#                 value=f"v{CURRENT_VERSION}",
#                 inline=True
#             )
#
#             embed.add_field(
#                 name="Nová verze",
#                 value=f"v{version}",
#                 inline=True
#             )
#
#             if len(release_notes) > 1024:
#                 release_notes = release_notes[:1021] + "..."
#
#             embed.add_field(
#                 name="Poznámky k vydání",
#                 value=release_notes,
#                 inline=False
#             )
#
#             embed.add_field(
#                 name="Jak aktualizovat",
#                 value=f"1. Přejděte do adresáře bota\n2. Zastavte aktuálního bota\n3. Spusťte `git pull`\n4. Restartujte bota",
#                 inline=False
#             )
#
#             embed.set_footer(text=f"GitHub: {GITHUB_REPO} | Vydáno: {release_data.get('published_at', 'neznámé datum')}")
#
#             await channel.send(embed=embed)
#             print(f"Sent update notification for new version {version}")
#         else:
#             # Bot is up to date
#             embed = discord.Embed(
#                 title=f"✅ Bot je aktuální",
#                 description=f"Bot je aktuální. Aktuální verze: v{version}",
#                 color=discord.Color.green(),
#                 url=release_url,
#                 timestamp=datetime.now().astimezone()
#             )
#
#             embed.add_field(
#                 name="Kontrola aktualizací",
#                 value=f"Další kontrola proběhne za {UPDATE_CHECK_INTERVAL_HOURS} hodin{'u' if UPDATE_CHECK_INTERVAL_HOURS == 1 else 'y'}.",
#                 inline=False
#             )
#
#             embed.set_footer(text=f"GitHub: {GITHUB_REPO}")
#
#             await channel.send(embed=embed)
#             print(f"Sent update status message - bot is up to date (version {version})")
#
#     @check_for_updates.before_loop
#     async def before_check_for_updates(self):
#         await self.bot.wait_until_ready()
#
#     @commands.command(name="checkupdate")
#     @commands.has_permissions(administrator=True)
#     async def check_update_command(self, ctx):
#         """Ručně zkontroluje, zda je k dispozici nová verze bota"""
#         await ctx.send("Kontroluji aktualizace...", ephemeral=True)
#
#         # Reset the last notification to force a new notification
#         db = self._load_db()
#         db["last_notification"] = None
#         self._save_db(db)
#
#         # Run the check
#         await self.check_for_updates()
#
#         await ctx.send("Kontrola aktualizací dokončena.", ephemeral=True)
#
# async def setup(bot):
#     await bot.add_cog(UpdateChecker(bot))

# Tento modul je momentálně deaktivován a bude zprovozněn později
# Funkce: Automatická kontrola aktualizací na GitHubu každou hodinu

import discord
from discord.ext import commands

class UpdateChecker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Update checker je deaktivován a bude zprovozněn později")

async def setup(bot):
    await bot.add_cog(UpdateChecker(bot))
