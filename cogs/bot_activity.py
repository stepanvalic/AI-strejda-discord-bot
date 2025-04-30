import discord
from discord.ext import commands, tasks
from utils import config

GUILD_ID = config.get_int('GUILD_ID')
ACTIVITY_TEXT_1 = config.get('ACTIVITY_TEXT_1', '{count} kočičkářů')
ACTIVITY_TEXT_2 = config.get('ACTIVITY_TEXT_2', '{count} darebáků')
ACTIVITY_TEXT_3 = config.get('ACTIVITY_TEXT_3', '{count} obránců cat army')

class BotActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_activity_index = 0
        self.change_status.start()

    def cog_unload(self):
        self.change_status.cancel()

    @tasks.loop(minutes=5)
    async def change_status(self):
        guild = self.bot.get_guild(GUILD_ID)
        member_count = guild.member_count if guild else 0

        # Rotace mezi třemi texty aktivity
        activity_texts = [ACTIVITY_TEXT_1, ACTIVITY_TEXT_2, ACTIVITY_TEXT_3]
        current_text = activity_texts[self.current_activity_index]
        status = current_text.format(count=member_count)

        # Přepnutí na další text pro příští volání
        self.current_activity_index = (self.current_activity_index + 1) % len(activity_texts)

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
