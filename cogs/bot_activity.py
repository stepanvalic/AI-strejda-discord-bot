import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv

load_dotenv()
GUILD_ID = int(os.getenv('GUILD_ID', 0))
ACTIVITY_BASE_TEXT = os.getenv('ACTIVITY_BASE_TEXT', 'Sleduji')
ACTIVITY_FORMAT_TEXT = os.getenv('ACTIVITY_FORMAT_TEXT', '{count} darebáků')

class BotActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_status.start()

    def cog_unload(self):
        self.change_status.cancel()

    @tasks.loop(minutes=5)
    async def change_status(self):
        guild = self.bot.get_guild(GUILD_ID)
        member_count = guild.member_count if guild else 0
        status = f"{ACTIVITY_BASE_TEXT} {ACTIVITY_FORMAT_TEXT.format(count=member_count)}"

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=status
            )
        )

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()

    @commands.command(name="setstatus")
    @commands.has_permissions(administrator=True)
    async def set_status(self, ctx, *, new_status: str):
        global ACTIVITY_BASE_TEXT
        ACTIVITY_BASE_TEXT = new_status
        await self.change_status()
        await ctx.send(f"Status changed to: {new_status}")

async def setup(bot):
    await bot.add_cog(BotActivity(bot))
