import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', 0))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is connected to {len(bot.guilds)} guilds')

    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        print(f'Bot is connected to the specified guild: {guild.name}')
    else:
        print(f'Warning: Bot is not connected to the specified guild ID: {GUILD_ID}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
        return

    print(f"Command error: {error}")
    await ctx.send(f"An error occurred: {error}")

@bot.command(name="shutdown", hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send("Shutting down the bot...")
    await bot.close()

async def load_extensions():
    await bot.load_extension("cogs.welcome")
    print("Loaded welcome cog")

    await bot.load_extension("cogs.bot_activity")
    print("Loaded bot activity cog")

    await bot.load_extension("cogs.youtube_video_ping")
    print("Loaded youtube video ping cog")

    await bot.load_extension("cogs.counting")
    print("Loaded counting cog")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
