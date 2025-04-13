import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        if not welcome_channel:
            print(f"Welcome channel with ID {WELCOME_CHANNEL_ID} not found!")
            return

        embed = discord.Embed(
            title=f"Vítej, {member.display_name}!",
            description=f"Zdravím na serveru AI Strejdy, {member.mention}!",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(text=f"ID: {member.id} • Připojil(a) se")
        embed.timestamp = member.joined_at

        await welcome_channel.send(embed=embed)

    @commands.command(name="welcome")
    @commands.has_permissions(administrator=True)
    async def manual_welcome(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        await self.on_member_join(member)
        await ctx.send(f"Sent welcome message for {member.display_name}!")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
