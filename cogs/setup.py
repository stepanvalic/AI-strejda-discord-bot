import os
import discord
import re
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
ENV_FILE = '.env'

# Načtení ID kanálů z .env souboru
try:
    YOUTUBE_NOTIFICATION_CHANNEL_ID = int(os.getenv('YOUTUBE_NOTIFICATION_CHANNEL_ID', 0))
except ValueError:
    YOUTUBE_NOTIFICATION_CHANNEL_ID = 0
    print("Warning: Invalid YOUTUBE_NOTIFICATION_CHANNEL_ID in .env file")

try:
    COUNTING_CHANNEL_ID = int(os.getenv('COUNTING_CHANNEL_ID', 0))
except ValueError:
    COUNTING_CHANNEL_ID = 0
    print("Warning: Invalid COUNTING_CHANNEL_ID in .env file")

try:
    WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
except ValueError:
    WELCOME_CHANNEL_ID = 0
    print("Warning: Invalid WELCOME_CHANNEL_ID in .env file")

def set_env_value(file_path, key, value):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    key_exists = False
    for i, line in enumerate(lines):
        if re.match(f'^{key}=.*', line):
            lines[i] = f'{key}={value}\n'
            key_exists = True
            break

    if not key_exists:
        lines.append(f'{key}={value}\n')

    with open(file_path, 'w') as file:
        file.writelines(lines)

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Všechny setup příkazy jsou zakomentovány a nejsou dostupné
    @commands.command(name="setupyoutube")
    @commands.has_permissions(administrator=True)
    async def setup_youtube(self, ctx):
        guild = ctx.guild

        channel_name = "【🔴】𝘆𝗼𝘂𝘁𝘂𝗯𝗲"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False),
            guild.me: discord.PermissionOverwrite(send_messages=True)
        }

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic="YouTube oznámení o nových videích"
            )

            set_env_value(ENV_FILE, "YOUTUBE_NOTIFICATION_CHANNEL_ID", str(channel.id))

            embed = discord.Embed(
                title="✅ YouTube kanál vytvořen",
                description=f"Kanál {channel.mention} byl úspěšně vytvořen a nastaven pro YouTube oznámení.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="Nastavení",
                value=f"ID kanálu: `{channel.id}`\nID bylo automaticky přidáno do .env souboru."
            )

            await ctx.send(embed=embed, ephemeral=True)

        except Exception as e:
            await ctx.send(f"Chyba při vytváření YouTube kanálu: {str(e)}", ephemeral=True)

    @commands.command(name="setupcounting")
    @commands.has_permissions(administrator=True)
    async def setup_counting(self, ctx):
        guild = ctx.guild

        channel_name = "【🎲】𝙥𝙤𝙘𝙞𝙩𝙖𝙣𝙞"

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                topic="Počítejte od 1 do nekonečna. Další číslo: 1"
            )

            set_env_value(ENV_FILE, "COUNTING_CHANNEL_ID", str(channel.id))

            embed = discord.Embed(
                title="✅ Counting kanál vytvořen",
                description=f"Kanál {channel.mention} byl úspěšně vytvořen a nastaven pro hru na počítání.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="Nastavení",
                value=f"ID kanálu: `{channel.id}`\nID bylo automaticky přidáno do .env souboru."
            )

            await ctx.send(embed=embed, ephemeral=True)

        except Exception as e:
            await ctx.send(f"Chyba při vytváření counting kanálu: {str(e)}", ephemeral=True)

    @commands.command(name="setupupdate")
    @commands.has_permissions(administrator=True)
    async def setup_update(self, ctx):
        guild = ctx.guild

        channel_name = "【📌】𝕤𝕚𝕧𝕪𝕒𝕡𝕚𝕯𝕒𝕘𝕚"

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                topic="Oznámení o aktualizacích bota"
            )

            set_env_value(ENV_FILE, "UPDATE_CHECK_CHANNEL_ID", str(channel.id))

            embed = discord.Embed(
                title="✅ Kanál pro aktualizace vytvořen",
                description=f"Kanál {channel.mention} byl úspěšně vytvořen a nastaven pro oznámení o aktualizacích.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="Nastavení",
                value=f"ID kanálu: `{channel.id}`\nID bylo automaticky přidáno do .env souboru."
            )

            await ctx.send(embed=embed, ephemeral=True)

        except Exception as e:
            await ctx.send(f"Chyba při vytváření kanálu pro aktualizace: {str(e)}", ephemeral=True)

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup_all(self, ctx):
        await self.setup_youtube(ctx)
        await self.setup_counting(ctx)
        await self.setup_update(ctx)
        await self.setup_audit_log(ctx)

        embed = discord.Embed(
            title="✅ Nastavení dokončeno",
            description="Všechny kanály byly úspěšně vytvořeny a nastaveny v .env souboru.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Nastavení",
            value="ID kanálů byla automaticky přidána do .env souboru.\n\n"
                  "Nezapomeňte nastavit ostatní proměnné v .env souboru:\n"
                  "- DISCORD_TOKEN\n"
                  "- GUILD_ID\n"
                  "- WELCOME_CHANNEL_ID\n"
                  "- YOUTUBE_API_KEY\n"
                  "- YOUTUBE_CHANNEL_ID"
        )

        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="setup_audit")
    @commands.has_permissions(administrator=True)
    async def setup_audit_log(self, ctx):
        # Vytvoříme kanál s oprávněními pouze pro administrátory
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        # Přidáme oprávnění pro role s admin právy
        for role in ctx.guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)

        try:
            channel = await ctx.guild.create_text_channel(
                name="audit-log",
                overwrites=overwrites,
                topic="Automatický audit log serveru"
            )

            # Aktualizujeme .env soubor
            self.update_env_variable("AUDIT_LOG_CHANNEL_ID", str(channel.id))

            await ctx.send(f"Vytvořen nový kanál pro audit log: {channel.mention}", ephemeral=True)

            # Vyvoláme příkaz setupaudit v audit_log cogu
            audit_cog = self.bot.get_cog("AuditLog")
            if audit_cog:
                await audit_cog.setup_audit(ctx, channel)

        except discord.Forbidden:
            await ctx.send("Nemám oprávnění vytvořit nový kanál.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.send(f"Nastala chyba při vytváření kanálu: {e}", ephemeral=True)

    @commands.command(name="setup_perms")
    @commands.has_permissions(administrator=True)
    async def setup_perms(self, ctx):
        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        guild = ctx.guild
        success_messages = []
        error_messages = []

        # Nastavení oprávnění pro YouTube kanál
        if YOUTUBE_NOTIFICATION_CHANNEL_ID != 0:
            try:
                youtube_channel = self.bot.get_channel(YOUTUBE_NOTIFICATION_CHANNEL_ID)
                if youtube_channel:
                    # Nastavení oprávnění: všichni vidí, pouze admin a bot mohou psát
                    await youtube_channel.set_permissions(guild.default_role, send_messages=False, view_channel=True)
                    await youtube_channel.set_permissions(guild.me, send_messages=True, view_channel=True)
                    success_messages.append(f"✅ Oprávnění pro YouTube kanál {youtube_channel.mention} byla nastavena.")
                else:
                    error_messages.append("❌ YouTube kanál nebyl nalezen.")
            except Exception as e:
                error_messages.append(f"❌ Chyba při nastavování oprávnění pro YouTube kanál: {str(e)}")
        else:
            error_messages.append("❌ ID YouTube kanálu není nastaveno v .env souboru.")

        # Nastavení oprávnění pro kanál na počítání
        if COUNTING_CHANNEL_ID != 0:
            try:
                counting_channel = self.bot.get_channel(COUNTING_CHANNEL_ID)
                if counting_channel:
                    # Nastavení oprávnění: všichni vidí a mohou psát, ale s limitem 15 sekund
                    await counting_channel.edit(slowmode_delay=15)
                    await counting_channel.set_permissions(guild.default_role, send_messages=True, view_channel=True)
                    success_messages.append(f"✅ Oprávnění pro kanál na počítání {counting_channel.mention} byla nastavena s limitem 15 sekund.")
                else:
                    error_messages.append("❌ Kanál na počítání nebyl nalezen.")
            except Exception as e:
                error_messages.append(f"❌ Chyba při nastavování oprávnění pro kanál na počítání: {str(e)}")
        else:
            error_messages.append("❌ ID kanálu na počítání není nastaveno v .env souboru.")

        # Nastavení oprávnění pro welcome kanál
        if WELCOME_CHANNEL_ID != 0:
            try:
                welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
                if welcome_channel:
                    # Nastavení oprávnění: všichni vidí, pouze admin a bot mohou psát
                    await welcome_channel.set_permissions(guild.default_role, send_messages=False, view_channel=True)
                    await welcome_channel.set_permissions(guild.me, send_messages=True, view_channel=True)
                    success_messages.append(f"✅ Oprávnění pro welcome kanál {welcome_channel.mention} byla nastavena.")
                else:
                    error_messages.append("❌ Welcome kanál nebyl nalezen.")
            except Exception as e:
                error_messages.append(f"❌ Chyba při nastavování oprávnění pro welcome kanál: {str(e)}")
        else:
            error_messages.append("❌ ID welcome kanálu není nastaveno v .env souboru.")

        # Vytvoření a odeslání embedu s výsledky
        embed = discord.Embed(
            title="🔧 Nastavení oprávnění kanálů",
            color=discord.Color.blue()
        )

        if success_messages:
            embed.add_field(
                name="✅ Úspěšné operace",
                value="\n".join(success_messages),
                inline=False
            )

        if error_messages:
            embed.add_field(
                name="❌ Chyby",
                value="\n".join(error_messages),
                inline=False
            )

        # Poslání zprávy přímo uživateli
        try:
            await ctx.author.send(embed=embed)
        except Exception as e:
            # Pokud nelze poslat DM, poslat zprávu do kanálu
            print(f"Chyba při posílání DM: {str(e)}")
            await ctx.send(f"{ctx.author.mention} Nastavení oprávnění bylo dokončeno.")

async def setup(bot):
    await bot.add_cog(Setup(bot))
