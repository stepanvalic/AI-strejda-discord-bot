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
        """Zobrazí kanál, kam teče nejlepší flow"""
        if YOUTUBE_NOTIFICATION_CHANNEL_ID == 0:
            await ctx.send("Kanál s nejlepší flow není nastaven v .env souboru.", ephemeral=True)
            return

        channel = self.bot.get_channel(YOUTUBE_NOTIFICATION_CHANNEL_ID)
        if not channel:
            await ctx.send("Kanál s nejlepší flow nebyl nalezen. Asi někdo vypnul vodovod!", ephemeral=True)
            return

        embed = discord.Embed(
            title="💧 Kanál s nejlepší flow",
            description=f"V tomto kanálu {channel.mention} teče ta nejlepší flow! Strejda by byl pyšný.",
            color=discord.Color.blue()
        )

        embed.set_footer(text="Pozor, vysoké riziko zatopit si boty!")

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="uptime")
    async def uptime(self, ctx):
        """Zobrazí, jak dlouho je bot online"""
        current_time = time.time()
        difference = int(current_time - START_TIME)

        uptime = datetime.timedelta(seconds=difference)

        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
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
            channel = ctx.channel
        else:
            channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
            if not channel:
                channel = ctx.channel

        try:
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

        # Kategorie příkazů
        utility_commands = {}
        moderation_commands = {}
        counting_commands = {}
        youtube_commands = {}
        ai_commands = {}
        other_commands = {}
        admin_commands = {}

        for command in self.bot.commands:
            if command.hidden:
                continue

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

            # Rozdělení příkazů do kategorií
            if requires_admin:
                admin_commands[cmd_name] = cmd_desc
            elif command.name in ["yt", "youtube", "kanal", "checkyoutube", "updatevideos"]:
                youtube_commands[cmd_name] = cmd_desc
            elif command.name in ["count", "countstats", "countrules", "countreset"]:
                counting_commands[cmd_name] = cmd_desc
            elif command.name in ["aiscore", "aitop", "aibottom", "airules", "aireset", "airesetall"]:
                ai_commands[cmd_name] = cmd_desc
            elif command.name in ["timeout", "untimeout", "unmute", "ban", "unban"]:
                moderation_commands[cmd_name] = cmd_desc
            elif command.name in ["uptime", "discord", "dc", "prikazy", "commands"]:
                utility_commands[cmd_name] = cmd_desc
            else:
                other_commands[cmd_name] = cmd_desc

        # Funkce pro přidání kategorie příkazů do embedu
        def add_commands_to_embed(commands_dict, category_name):
            if not commands_dict:
                return

            commands_text = ""
            for cmd, desc in commands_dict.items():
                commands_text += f"**{cmd}** - {desc}\n"
            embed.add_field(name=category_name, value=commands_text, inline=False)

        # Přidání kategorií do embedu
        add_commands_to_embed(utility_commands, "Užitečné příkazy")
        add_commands_to_embed(youtube_commands, "YouTube příkazy")
        add_commands_to_embed(counting_commands, "Počítací příkazy")
        add_commands_to_embed(ai_commands, "AI Moderace příkazy")
        add_commands_to_embed(moderation_commands, "Moderační příkazy")
        add_commands_to_embed(other_commands, "Ostatní příkazy")
        add_commands_to_embed(admin_commands, "Admin příkazy")

        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))
