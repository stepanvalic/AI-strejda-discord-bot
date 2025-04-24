import time
import datetime
import discord
from discord.ext import commands
import config

# Get configuration from config.py
YOUTUBE_CHANNEL = config.YOUTUBE_CHANNEL_ID
YOUTUBE_NOTIFICATION_CHANNEL_ID = config.YOUTUBE_NOTIFICATION_CHANNEL_ID
WELCOME_CHANNEL_ID = config.WELCOME_CHANNEL_ID

START_TIME = time.time()

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="yt", aliases=["youtube"])
    async def youtube_channel(self, ctx):
        """Zobrazí odkaz na YouTube kanál"""
        # Kontrola, zda je YouTube kanál nastaven
        if not YOUTUBE_CHANNEL:
            await ctx.send("YouTube kanál není nastaven v .env souboru.", ephemeral=True)
            return

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

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
            elif command.name in ["uptime", "discord", "dc", "prikazy", "commands", "help"]:
                utility_commands[cmd_name] = cmd_desc
            elif command.name in ["sumarizace-stepan", "ytlastvideosend"]:
                admin_commands[cmd_name] = cmd_desc
            else:
                other_commands[cmd_name] = cmd_desc

        # Funkce pro přidání kategorie příkazů do embedu
        def add_commands_to_embed(commands_dict, category_name):
            if not commands_dict:
                return

            # Maximální délka hodnoty pole v embedu
            max_field_length = 1000  # Použijeme 1000 místo 1024 pro jistotu

            commands_text = ""
            part_num = 1

            for cmd, desc in commands_dict.items():
                line = f"**{cmd}** - {desc}\n"

                # Pokud by přidání této řádky překročilo limit, vytvoříme nové pole
                if len(commands_text) + len(line) > max_field_length:
                    # Přidáme aktuální text jako pole
                    field_name = category_name if part_num == 1 else f"{category_name} (pokračování {part_num})"
                    embed.add_field(name=field_name, value=commands_text, inline=False)

                    # Resetujeme text a zvýšíme číslo části
                    commands_text = line
                    part_num += 1
                else:
                    commands_text += line

            # Přidáme poslední pole, pokud obsahuje nějaký text
            if commands_text:
                field_name = category_name if part_num == 1 else f"{category_name} (pokračování {part_num})"
                embed.add_field(name=field_name, value=commands_text, inline=False)

        # Přidání kategorií do embedu
        add_commands_to_embed(utility_commands, "Užitečné příkazy")
        add_commands_to_embed(youtube_commands, "YouTube příkazy")
        add_commands_to_embed(counting_commands, "Počítací příkazy")
        add_commands_to_embed(ai_commands, "AI Moderace příkazy")
        add_commands_to_embed(moderation_commands, "Moderační příkazy")
        add_commands_to_embed(other_commands, "Ostatní příkazy")
        add_commands_to_embed(admin_commands, "Admin příkazy")

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Zobrazí nápovědu pro běžné uživatele"""
        embed = discord.Embed(
            title="Nápověda pro uživatele",
            description="Zde je seznam příkazů pro běžné uživatele:",
            color=discord.Color.blue()
        )

        # Kategorie příkazů
        utility_commands = {}
        counting_commands = {}
        youtube_commands = {}
        ai_commands = {}
        other_commands = {}

        for command in self.bot.commands:
            if command.hidden:
                continue

            # Přeskočit admin příkazy
            requires_admin = False
            for check in command.checks:
                if "administrator" in str(check) or "is_owner" in str(check):
                    requires_admin = True
                    break

            if requires_admin:
                continue

            cmd_desc = command.help or "Žádný popis"
            cmd_name = f"!{command.name}"

            if command.aliases:
                aliases = ", !".join(command.aliases)
                cmd_name += f" (nebo !{aliases})"

            # Rozdělení příkazů do kategorií (pouze uživatelské příkazy)
            if command.name in ["yt", "youtube", "kanal"]:
                youtube_commands[cmd_name] = cmd_desc
            elif command.name in ["countrules", "countstats"]:
                counting_commands[cmd_name] = cmd_desc
            elif command.name in ["aiscore", "aitop", "aibottom"]:
                ai_commands[cmd_name] = cmd_desc
            elif command.name in ["uptime", "discord", "dc", "help"]:
                utility_commands[cmd_name] = cmd_desc
            else:
                # Přeskočit moderační příkazy
                if command.name not in ["timeout", "untimeout", "unmute", "ban", "unban", "prikazy", "commands"]:
                    other_commands[cmd_name] = cmd_desc

        # Funkce pro přidání kategorie příkazů do embedu
        def add_commands_to_embed(commands_dict, category_name):
            if not commands_dict:
                return

            # Maximální délka hodnoty pole v embedu
            max_field_length = 1000  # Použijeme 1000 místo 1024 pro jistotu

            commands_text = ""
            part_num = 1

            for cmd, desc in commands_dict.items():
                line = f"**{cmd}** - {desc}\n"

                # Pokud by přidání této řádky překročilo limit, vytvoříme nové pole
                if len(commands_text) + len(line) > max_field_length:
                    # Přidáme aktuální text jako pole
                    field_name = category_name if part_num == 1 else f"{category_name} (pokračování {part_num})"
                    embed.add_field(name=field_name, value=commands_text, inline=False)

                    # Resetujeme text a zvýšíme číslo části
                    commands_text = line
                    part_num += 1
                else:
                    commands_text += line

            # Přidáme poslední pole, pokud obsahuje nějaký text
            if commands_text:
                field_name = category_name if part_num == 1 else f"{category_name} (pokračování {part_num})"
                embed.add_field(name=field_name, value=commands_text, inline=False)

        # Přidání kategorií do embedu
        add_commands_to_embed(utility_commands, "Užitečné příkazy")
        add_commands_to_embed(youtube_commands, "YouTube příkazy")
        add_commands_to_embed(counting_commands, "Počítací příkazy")
        add_commands_to_embed(ai_commands, "AI Moderace příkazy")
        add_commands_to_embed(other_commands, "Ostatní příkazy")

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        await ctx.send(embed=embed)

    @commands.command(name="pravidla")
    @commands.has_permissions(administrator=True)
    async def server_rules(self, ctx, channel_id: str = None):
        """Zobrazí pravidla serveru ve dvou embedech (admin only)"""
        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        # Určení cílového kanálu
        target_channel = None
        if channel_id:
            try:
                channel_id = int(channel_id)
                target_channel = self.bot.get_channel(channel_id)
            except ValueError:
                await ctx.send("Neplatné ID kanálu. Zadej platné číselné ID.", ephemeral=True)
                return

        if not target_channel:
            target_channel = ctx.channel

        # Vytvoření embedu s obecnými pravidly
        general_rules_embed = discord.Embed(
            title="📜 Pravidla serveru",
            description="Prosím, dodržujte tato pravidla pro udržení přátelské a bezpečné komunity.",
            color=discord.Color.blue()
        )

        general_rules_embed.add_field(
            name="1. Buďte k sobě slušní",
            value="Chovejte se k ostatním s respektem. Není tolerováno obtěžování, ublížení nebo jiné nevhodné chování.",
            inline=False
        )

        general_rules_embed.add_field(
            name="2. Žádné nevhodné nebo urážlivé obsah",
            value="Nezveřejňujte obsah, který je sexuální, násilný, rasistický nebo jinak nevhodný.",
            inline=False
        )

        general_rules_embed.add_field(
            name="3. Žádný spam nebo sebepropagace",
            value="Nezahlcujte kanály opakovanými zprávami nebo nevhodnými odkazy. Sebepropagace je povolena pouze v určených kanálech.",
            inline=False
        )

        general_rules_embed.add_field(
            name="4. Používejte správné kanály",
            value="Posílejte zprávy do odpovídajících kanálů podle jejich tématu.",
            inline=False
        )

        general_rules_embed.add_field(
            name="5. Respektujte moderátory",
            value="Moderátoři jsou zde, aby udržovali pořádek. Respektujte jejich rozhodnutí a pokyny.",
            inline=False
        )

        general_rules_embed.set_footer(text="Porušení pravidel může vést k varovaní, dočasnému nebo trvalému zabanování.")

        # Vytvoření embedu s pravidly AI hlídače
        ai_rules_embed = discord.Embed(
            title="🤖 AI Hlídač - Pravidla a bodování",
            description="Náš server používá AI systém pro hodnocení chování uživatelů. Zde je vysvětlení, jak funguje:",
            color=discord.Color.purple()
        )

        ai_rules_embed.add_field(
            name="💬 Analýza zpráv",
            value="AI analyzuje vaše zprávy a hodnotit jejich sentiment (pozitivní nebo negativní). Za pozitivní komunikaci získáváte body, za negativní je ztrácíte.",
            inline=False
        )

        ai_rules_embed.add_field(
            name="🌟 Odměny za pozitivní chování",
            value="**Úroveň 1:** 800+ bodů - získáte speciální roli\n"
                  "**Úroveň 2:** 2000+ bodů - získáte pokročilejší roli\n"
                  "**Úroveň 3:** 5000+ bodů - získáte nejvyšší roli",
            inline=False
        )

        ai_rules_embed.add_field(
            name="⚠️ Postihy za negativní chování",
            value="**Timeout:** -30 bodů - dočasný timeout\n"
                  "**Negativní role:** -1000 bodů - přidělení negativní role\n"
                  "**Extra postih:** -50 bodů za každou velmi negativní zprávu",
            inline=False
        )

        ai_rules_embed.add_field(
            name="📊 Kontrola vašeho skóre",
            value="Použijte příkaz `!aiscore` pro zobrazení vašeho aktuálního skóre.\n"
                  "`!aitop` zobrazí žebříček nejlepších uživatelů.\n"
                  "`!aibottom` zobrazí uživatele s nejnižším skóre.",
            inline=False
        )

        ai_rules_embed.add_field(
            name="🔍 Sledované chování",
            value="AI sleduje zejména:\n"
                  "- Urážlivý jazyk a nadávky\n"
                  "- Rasistické a diskriminační výrazy\n"
                  "- Obtěžování a vyhrožování\n"
                  "- Pozitivní a nápomocné příspěvky\n"
                  "- Přátelské a konstruktivní diskuze",
            inline=False
        )

        ai_rules_embed.set_footer(text="AI moderátor je zde, aby pomohl udržet přátelskou atmosféru, ne aby vás trestal. Buďte k sobě milí!")

        # Odeslání embedů
        await target_channel.send(embed=general_rules_embed)
        await target_channel.send(embed=ai_rules_embed)

        # Potvrzení pro admina
        if target_channel != ctx.channel:
            await ctx.send(f"Pravidla byla odeslána do kanálu {target_channel.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))
