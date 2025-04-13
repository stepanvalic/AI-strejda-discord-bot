import os
import time
import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_CHANNEL = os.getenv('YOUTUBE_CHANNEL_ID', '@davidstrejc')
try:
    YOUTUBE_NOTIFICATION_CHANNEL_ID = int(os.getenv('YOUTUBE_NOTIFICATION_CHANNEL_ID', 0))
except ValueError:
    YOUTUBE_NOTIFICATION_CHANNEL_ID = 0
    print("Warning: Invalid YOUTUBE_NOTIFICATION_CHANNEL_ID in .env file")

try:
    WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
except ValueError:
    WELCOME_CHANNEL_ID = 0
    print("Warning: Invalid WELCOME_CHANNEL_ID in .env file")

# Store bot start time
START_TIME = time.time()

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="yt", aliases=["youtube"])
    async def youtube_channel(self, ctx):
        """Zobrazí odkaz na YouTube kanál"""
        channel_url = f"https://www.youtube.com/{YOUTUBE_CHANNEL}" if YOUTUBE_CHANNEL.startswith('@') else f"https://www.youtube.com/channel/{YOUTUBE_CHANNEL}"
        
        embed = discord.Embed(
            title="YouTube kanál",
            description=f"Zde je odkaz na YouTube kanál: [**{YOUTUBE_CHANNEL}**]({channel_url})",
            color=discord.Color.red()
        )
        
        embed.set_thumbnail(url="https://s.ytimg.com/yts/img/favicon_144-vfliLAfaB.png")
        
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="kanal")
    async def youtube_notification_channel(self, ctx):
        """Zobrazí kanál, kam tečou YouTube notifikace"""
        if YOUTUBE_NOTIFICATION_CHANNEL_ID == 0:
            await ctx.send("YouTube notifikační kanál není nastaven v .env souboru.", ephemeral=True)
            return
            
        channel = self.bot.get_channel(YOUTUBE_NOTIFICATION_CHANNEL_ID)
        if not channel:
            await ctx.send("YouTube notifikační kanál nebyl nalezen.", ephemeral=True)
            return
            
        embed = discord.Embed(
            title="YouTube notifikační kanál",
            description=f"YouTube notifikace jsou posílány do kanálu {channel.mention}",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Zobrazí, jak dlouho je bot online"""
        current_time = time.time()
        difference = int(current_time - START_TIME)
        
        # Convert to datetime.timedelta for easier formatting
        uptime = datetime.timedelta(seconds=difference)
        
        # Format days, hours, minutes, seconds
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Create a formatted string
        uptime_str = ""
        if days > 0:
            uptime_str += f"{days} {'dní' if days != 1 else 'den'}, "
        if hours > 0:
            uptime_str += f"{hours} {'hodin' if hours != 1 else 'hodina'}, "
        if minutes > 0:
            uptime_str += f"{minutes} {'minut' if minutes != 1 else 'minuta'}, "
        uptime_str += f"{seconds} {'sekund' if seconds != 1 else 'sekunda'}"
        
        embed = discord.Embed(
            title="🕒 Uptime bota",
            description=f"Bot běží již: **{uptime_str}**",
            color=discord.Color.blue()
        )
        
        embed.set_footer(text=f"Bot byl spuštěn: {datetime.datetime.fromtimestamp(START_TIME).strftime('%d.%m.%Y %H:%M:%S')}")
        
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="discord", aliases=["dc"])
    async def discord_invite(self, ctx):
        """Vygeneruje pozvánku na Discord server"""
        if WELCOME_CHANNEL_ID == 0:
            # If welcome channel is not set, use the current channel
            channel = ctx.channel
        else:
            channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
            if not channel:
                # If welcome channel is not found, use the current channel
                channel = ctx.channel
        
        try:
            # Create an invite that never expires
            invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)
            
            embed = discord.Embed(
                title="Discord pozvánka",
                description=f"Zde je pozvánka na náš Discord server: {invite.url}",
                color=discord.Color.blurple()
            )
            
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            
            await ctx.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await ctx.send("Nemám oprávnění vytvářet pozvánky.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Chyba při vytváření pozvánky: {str(e)}", ephemeral=True)

    @commands.command(name="prikazy", aliases=["commands"])
    async def list_commands(self, ctx):
        """Zobrazí seznam všech příkazů"""
        embed = discord.Embed(
            title="Seznam příkazů",
            description="Zde je seznam všech dostupných příkazů:",
            color=discord.Color.green()
        )
        
        # Get all commands
        all_commands = {}
        admin_commands = {}
        
        for command in self.bot.commands:
            # Skip hidden commands
            if command.hidden:
                continue
                
            # Check if command requires admin permissions
            requires_admin = False
            for check in command.checks:
                if "administrator" in str(check):
                    requires_admin = True
                    break
            
            cmd_desc = command.help or "Žádný popis"
            cmd_name = f"!{command.name}"
            
            if command.aliases:
                aliases = ", !".join(command.aliases)
                cmd_name += f" (nebo !{aliases})"
            
            if requires_admin:
                admin_commands[cmd_name] = cmd_desc
            else:
                all_commands[cmd_name] = cmd_desc
        
        # Add regular commands
        if all_commands:
            commands_text = ""
            for cmd, desc in all_commands.items():
                commands_text += f"**{cmd}** - {desc}\n"
            embed.add_field(name="Běžné příkazy", value=commands_text, inline=False)
        
        # Add admin commands
        if admin_commands:
            admin_commands_text = ""
            for cmd, desc in admin_commands.items():
                admin_commands_text += f"**{cmd}** - {desc}\n"
            embed.add_field(name="Admin příkazy", value=admin_commands_text, inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))
