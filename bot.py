import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{Fore.GREEN}{Style.BRIGHT}🤖 {bot.user.name} has connected to Discord!{Style.RESET_ALL}')
    print(f'{Fore.CYAN}Bot is connected to {Fore.YELLOW}{len(bot.guilds)}{Fore.CYAN} guilds')

    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        print(f'{Fore.CYAN}Bot is connected to the specified guild: {Fore.YELLOW}{guild.name}{Style.RESET_ALL}')
    else:
        print(f'{Fore.RED}{Style.BRIGHT}⚠️ Warning: Bot is not connected to the specified guild ID: {GUILD_ID}{Style.RESET_ALL}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
        return

    print(f"{Fore.RED}{Style.BRIGHT}❌ Command error: {error}{Style.RESET_ALL}")
    await ctx.send(f"An error occurred: {error}")

@bot.command(name="shutdown", hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("Shutting down the bot...")
    await bot.close()

async def load_extensions():
    await bot.load_extension("cogs.welcome")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}welcome{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.bot_activity")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}bot_activity{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.youtube_video_ping")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}youtube_video_ping{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.counting")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}counting{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.setup")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}setup{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.utility")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}utility{Fore.MAGENTA} cog")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
