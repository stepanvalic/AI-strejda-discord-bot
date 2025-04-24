import discord
from discord.ext import commands, tasks
import config

class BotActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_status.start()

    def cog_unload(self):
        self.change_status.cancel()

    @tasks.loop(minutes=5)
    async def change_status(self):
        guild = self.bot.get_guild(config.GUILD_ID)
        member_count = guild.member_count if guild else 0
        status = f"{config.ACTIVITY_BASE_TEXT} {config.ACTIVITY_FORMAT_TEXT.format(count=member_count)}"

        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=status
            )
        )

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BotActivity(bot))
