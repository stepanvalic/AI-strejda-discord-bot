import discord
from discord.ext import commands
import colorama
from colorama import Fore, Back, Style
import asyncio
import signal
import sys
import logging
from utils.permissions import check_permissions
from utils import config

colorama.init(autoreset=True)

# Configure logging to suppress aiohttp SSL warnings
logging.getLogger('aiohttp.client').setLevel(logging.WARNING)
logging.getLogger('discord.client').setLevel(logging.WARNING)

TOKEN = config.get('DISCORD_TOKEN')
GUILD_ID = config.get_int('GUILD_ID')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

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

    if await check_permissions(ctx, error):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
        return

    print(f"{Fore.RED}{Style.BRIGHT}❌ Command error: {error}{Style.RESET_ALL}")
    await ctx.send(f"An error occurred: {error}")

@bot.command(name="shutdown", hidden=True)
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    """Vypne bota (admin only)"""
    await ctx.send("Shutting down the bot...")
    await graceful_shutdown()

async def graceful_shutdown():
    """Gracefully shutdown the bot with proper cleanup"""
    print(f"{Fore.YELLOW}🔄 Initiating graceful shutdown...{Style.RESET_ALL}")
    
    try:
        # Close all cogs properly
        for cog_name in list(bot.cogs.keys()):
            try:
                await bot.unload_extension(f"cogs.{cog_name.lower()}")
                print(f"{Fore.CYAN}✅ Unloaded cog: {cog_name}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Error unloading cog {cog_name}: {e}{Style.RESET_ALL}")
        
        # Close the bot connection
        if not bot.is_closed():
            await bot.close()
            print(f"{Fore.GREEN}✅ Bot connection closed{Style.RESET_ALL}")
        
        # Wait a bit for cleanup
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f"{Fore.RED}❌ Error during shutdown: {e}{Style.RESET_ALL}")
    
    print(f"{Fore.GREEN}🔄 Shutdown complete{Style.RESET_ALL}")

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    print(f"\n{Fore.YELLOW}🛑 Received signal {signum}, initiating shutdown...{Style.RESET_ALL}")
    asyncio.create_task(graceful_shutdown())

async def load_extensions():
    await bot.load_extension("cogs.welcome")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}welcome{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.bot_activity")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}bot_activity{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.youtube_ping")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}youtube_ping{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.counting")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}counting{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.setup")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}setup{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.utility")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}utility{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.moderation")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}moderation{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.ai_moderation")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}ai_moderation{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.audit_log")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}audit_log{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.word_filter")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}word_filter{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.chat_summary")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}chat_summary{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.logger")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}logger{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.bookmarks")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}bookmarks{Fore.MAGENTA} cog")

    await bot.load_extension("cogs.reaction_roles")
    print(f"{Fore.MAGENTA}✅ Loaded {Fore.CYAN}reaction_roles{Fore.MAGENTA} cog")

async def main():
    # Set up signal handlers for graceful shutdown
    if sys.platform != 'win32':
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        async with bot:
            await load_extensions()
            print(f"{Fore.GREEN}🚀 Starting bot...{Style.RESET_ALL}")
            await bot.start(TOKEN)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 KeyboardInterrupt received{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
    finally:
        if not bot.is_closed():
            await graceful_shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🛑 Bot shutdown complete{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Fatal error: {e}{Style.RESET_ALL}")
    finally:
        sys.exit(0)
