import discord
from discord.ext import commands
import os
import datetime
import asyncio
from utils import config

# Načtení proměnných z konfigurace
AUDIT_LOG_CHANNEL_ID = config.get_int('AUDIT_LOG_CHANNEL_ID')
GUILD_ID = config.get_int('GUILD_ID')
COUNTING_CHANNEL_ID = config.get_int('COUNTING_CHANNEL_ID')

class AuditLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audit_channel = None
        self.message_cache = {}  # Cache pro sledování zpráv pro detekci úprav
        self.max_cache_size = 1000  # Maximální velikost cache

    @commands.Cog.listener()
    async def on_ready(self):
        """Inicializace po připravení bota"""
        if AUDIT_LOG_CHANNEL_ID:
            self.audit_channel = self.bot.get_channel(AUDIT_LOG_CHANNEL_ID)
            if self.audit_channel:
                print(f"Audit log kanál nastaven: #{self.audit_channel.name}")
            else:
                print(f"Varování: Audit log kanál s ID {AUDIT_LOG_CHANNEL_ID} nebyl nalezen!")
        else:
            print("Audit log kanál není nastaven v .env souboru (AUDIT_LOG_CHANNEL_ID)")

    async def send_log(self, embed):
        """Odešle audit log do určeného kanálu"""
        if not self.audit_channel:
            # Pokud kanál není nastaven, zkusíme ho znovu získat
            if AUDIT_LOG_CHANNEL_ID:
                self.audit_channel = self.bot.get_channel(AUDIT_LOG_CHANNEL_ID)

            # Pokud stále není k dispozici, vrátíme se
            if not self.audit_channel:
                return

        try:
            await self.audit_channel.send(embed=embed)
        except discord.Forbidden:
            print("Bot nemá oprávnění posílat zprávy do audit log kanálu")
        except discord.HTTPException as e:
            print(f"Chyba při odesílání audit logu: {e}")

    def create_embed(self, title, description, color=discord.Color.blue()):
        """Vytvoří základní embed pro audit log"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.now()
        )
        return embed

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Sleduje úpravy zpráv"""
        # Ignorujeme zprávy od botů a soukromé zprávy
        if before.author.bot or not before.guild:
            return

        # Ignorujeme zprávy v kanálu počítání
        if before.channel.id == COUNTING_CHANNEL_ID:
            return

        # Ignorujeme, pokud se obsah nezměnil (např. embed se načetl)
        if before.content == after.content:
            return

        embed = self.create_embed(
            "✏️ Zpráva upravena",
            f"**Uživatel:** {before.author.mention} ({before.author.name})\n"
            f"**Kanál:** {before.channel.mention}\n"
            f"[Přejít na zprávu]({after.jump_url})",
            discord.Color.gold()
        )

        # Přidáme původní a nový obsah zprávy
        if len(before.content) > 1024:
            embed.add_field(name="Původní zpráva", value=f"{before.content[:1021]}...", inline=False)
        else:
            embed.add_field(name="Původní zpráva", value=before.content or "(prázdná zpráva)", inline=False)

        if len(after.content) > 1024:
            embed.add_field(name="Nová zpráva", value=f"{after.content[:1021]}...", inline=False)
        else:
            embed.add_field(name="Nová zpráva", value=after.content or "(prázdná zpráva)", inline=False)

        embed.set_footer(text=f"ID uživatele: {before.author.id} • ID zprávy: {before.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Sleduje mazání zpráv"""
        # Ignorujeme zprávy od botů a soukromé zprávy
        if message.author.bot or not message.guild:
            return

        # Ignorujeme zprávy v kanálu počítání
        if message.channel.id == COUNTING_CHANNEL_ID:
            return

        embed = self.create_embed(
            "🗑️ Zpráva smazána",
            f"**Uživatel:** {message.author.mention} ({message.author.name})\n"
            f"**Kanál:** {message.channel.mention}",
            discord.Color.red()
        )

        # Přidáme obsah smazané zprávy
        if len(message.content) > 1024:
            embed.add_field(name="Obsah zprávy", value=f"{message.content[:1021]}...", inline=False)
        else:
            embed.add_field(name="Obsah zprávy", value=message.content or "(prázdná zpráva)", inline=False)

        # Přidáme přílohy, pokud existují
        if message.attachments:
            attachment_list = "\n".join([f"[{a.filename}]({a.proxy_url})" for a in message.attachments])
            embed.add_field(name="Přílohy", value=attachment_list, inline=False)

        embed.set_footer(text=f"ID uživatele: {message.author.id} • ID zprávy: {message.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Sleduje změny u členů (přezdívky, role)"""
        # Ignorujeme změny u botů
        if before.bot:
            return

        # Kontrola změny přezdívky
        if before.nick != after.nick:
            embed = self.create_embed(
                "👤 Přezdívka změněna",
                f"**Uživatel:** {after.mention} ({after.name})",
                discord.Color.blue()
            )

            embed.add_field(name="Původní přezdívka", value=before.nick or "(žádná přezdívka)", inline=True)
            embed.add_field(name="Nová přezdívka", value=after.nick or "(žádná přezdívka)", inline=True)
            embed.set_footer(text=f"ID uživatele: {after.id}")

            await self.send_log(embed)

        # Kontrola změny rolí
        if before.roles != after.roles:
            # Zjistíme, které role byly přidány a které odebrány
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles:
                embed = self.create_embed(
                    "🛡️ Role přidány",
                    f"**Uživatel:** {after.mention} ({after.name})",
                    discord.Color.green()
                )

                roles_text = ", ".join([role.mention for role in added_roles])
                embed.add_field(name="Přidané role", value=roles_text, inline=False)
                embed.set_footer(text=f"ID uživatele: {after.id}")

                await self.send_log(embed)

            if removed_roles:
                embed = self.create_embed(
                    "🛡️ Role odebrány",
                    f"**Uživatel:** {after.mention} ({after.name})",
                    discord.Color.orange()
                )

                roles_text = ", ".join([role.mention for role in removed_roles])
                embed.add_field(name="Odebrané role", value=roles_text, inline=False)
                embed.set_footer(text=f"ID uživatele: {after.id}")

                await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Sleduje vytváření kanálů"""
        embed = self.create_embed(
            "📝 Kanál vytvořen",
            f"**Název:** {channel.name}\n"
            f"**Typ:** {self.get_channel_type(channel)}\n"
            f"**Kategorie:** {channel.category.name if channel.category else 'Žádná'}",
            discord.Color.green()
        )

        embed.set_footer(text=f"ID kanálu: {channel.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Sleduje mazání kanálů"""
        embed = self.create_embed(
            "🗑️ Kanál smazán",
            f"**Název:** {channel.name}\n"
            f"**Typ:** {self.get_channel_type(channel)}\n"
            f"**Kategorie:** {channel.category.name if channel.category else 'Žádná'}",
            discord.Color.red()
        )

        embed.set_footer(text=f"ID kanálu: {channel.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Sleduje změny kanálů"""
        # Ignorujeme kanál počítání
        if before.id == COUNTING_CHANNEL_ID:
            return

        changes = []

        # Kontrola změny názvu
        if before.name != after.name:
            changes.append(f"**Název:** {before.name} → {after.name}")

        # Kontrola změny tématu (pouze pro textové kanály)
        if hasattr(before, 'topic') and hasattr(after, 'topic') and before.topic != after.topic:
            before_topic = before.topic or "(žádné téma)"
            after_topic = after.topic or "(žádné téma)"
            changes.append(f"**Téma:** {before_topic} → {after_topic}")

        # Kontrola změny kategorie
        if before.category != after.category:
            before_category = before.category.name if before.category else "Žádná"
            after_category = after.category.name if after.category else "Žádná"
            changes.append(f"**Kategorie:** {before_category} → {after_category}")

        # Kontrola změny oprávnění
        if before.overwrites != after.overwrites:
            changes.append("**Oprávnění:** Změněna oprávnění kanálu")

        # Kontrola změny pomalého režimu
        if hasattr(before, 'slowmode_delay') and hasattr(after, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
            before_slowmode = f"{before.slowmode_delay} sekund" if before.slowmode_delay > 0 else "Vypnuto"
            after_slowmode = f"{after.slowmode_delay} sekund" if after.slowmode_delay > 0 else "Vypnuto"
            changes.append(f"**Pomalý režim:** {before_slowmode} → {after_slowmode}")

        # Pokud byly zjištěny změny, vytvoříme log
        if changes:
            embed = self.create_embed(
                "🔄 Kanál aktualizován",
                f"**Kanál:** {after.mention}\n" + "\n".join(changes),
                discord.Color.gold()
            )

            embed.set_footer(text=f"ID kanálu: {after.id}")

            await self.send_log(embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Sleduje bany uživatelů"""
        embed = self.create_embed(
            "🔨 Uživatel zabanován",
            f"**Uživatel:** {user.mention} ({user.name})",
            discord.Color.dark_red()
        )

        # Pokusíme se získat záznam z audit logu pro zjištění důvodu a moderátora
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    embed.add_field(name="Zabanoval", value=f"{entry.user.mention} ({entry.user.name})", inline=True)
                    if entry.reason:
                        embed.add_field(name="Důvod", value=entry.reason, inline=True)
                    break
        except discord.Forbidden:
            pass  # Bot nemá oprávnění číst audit log

        embed.set_footer(text=f"ID uživatele: {user.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Sleduje unbany uživatelů"""
        embed = self.create_embed(
            "🔓 Uživatel odbanován",
            f"**Uživatel:** {user.name} ({user.id})",
            discord.Color.green()
        )

        # Pokusíme se získat záznam z audit logu pro zjištění moderátora
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    embed.add_field(name="Odbanoval", value=f"{entry.user.mention} ({entry.user.name})", inline=True)
                    if entry.reason:
                        embed.add_field(name="Důvod", value=entry.reason, inline=True)
                    break
        except discord.Forbidden:
            pass  # Bot nemá oprávnění číst audit log

        embed.set_footer(text=f"ID uživatele: {user.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Sleduje vytváření rolí"""
        embed = self.create_embed(
            "🛡️ Role vytvořena",
            f"**Název:** {role.name}\n"
            f"**Barva:** {role.color}\n"
            f"**Pozice:** {role.position}",
            discord.Color.green()
        )

        # Pokusíme se získat záznam z audit logu pro zjištění moderátora
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    embed.add_field(name="Vytvořil", value=f"{entry.user.mention} ({entry.user.name})", inline=True)
                    break
        except discord.Forbidden:
            pass  # Bot nemá oprávnění číst audit log

        embed.set_footer(text=f"ID role: {role.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Sleduje mazání rolí"""
        embed = self.create_embed(
            "🗑️ Role smazána",
            f"**Název:** {role.name}\n"
            f"**Barva:** {role.color}\n"
            f"**Pozice:** {role.position}",
            discord.Color.red()
        )

        # Pokusíme se získat záznam z audit logu pro zjištění moderátora
        try:
            async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    embed.add_field(name="Smazal", value=f"{entry.user.mention} ({entry.user.name})", inline=True)
                    break
        except discord.Forbidden:
            pass  # Bot nemá oprávnění číst audit log

        embed.set_footer(text=f"ID role: {role.id}")

        await self.send_log(embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Sleduje změny rolí"""
        changes = []

        # Kontrola změny názvu
        if before.name != after.name:
            changes.append(f"**Název:** {before.name} → {after.name}")

        # Kontrola změny barvy
        if before.color != after.color:
            changes.append(f"**Barva:** {before.color} → {after.color}")

        # Kontrola změny oprávnění
        if before.permissions != after.permissions:
            changes.append("**Oprávnění:** Změněna oprávnění role")

        # Kontrola změny pozice
        if before.position != after.position:
            changes.append(f"**Pozice:** {before.position} → {after.position}")

        # Kontrola změny viditelnosti
        if before.hoist != after.hoist:
            before_hoist = "Ano" if before.hoist else "Ne"
            after_hoist = "Ano" if after.hoist else "Ne"
            changes.append(f"**Zobrazena odděleně:** {before_hoist} → {after_hoist}")

        # Kontrola změny mentionovatelnosti
        if before.mentionable != after.mentionable:
            before_mentionable = "Ano" if before.mentionable else "Ne"
            after_mentionable = "Ano" if after.mentionable else "Ne"
            changes.append(f"**Mentionovatelná:** {before_mentionable} → {after_mentionable}")

        # Pokud byly zjištěny změny, vytvoříme log
        if changes:
            embed = self.create_embed(
                "🔄 Role aktualizována",
                f"**Role:** {after.mention}\n" + "\n".join(changes),
                discord.Color.gold()
            )

            # Pokusíme se získat záznam z audit logu pro zjištění moderátora
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                    if entry.target.id == after.id:
                        embed.add_field(name="Upravil", value=f"{entry.user.mention} ({entry.user.name})", inline=True)
                        break
            except discord.Forbidden:
                pass  # Bot nemá oprávnění číst audit log

            embed.set_footer(text=f"ID role: {after.id}")

            await self.send_log(embed)

    @commands.Cog.listener()
    async def on_member_timeout(self, member, until):
        """Sleduje timeouty uživatelů (vlastní event, který je třeba vyvolat z moderation.py)"""
        if until:
            # Timeout byl aplikován
            duration = until - datetime.datetime.now(datetime.timezone.utc)
            duration_str = self.format_duration(duration.total_seconds())

            embed = self.create_embed(
                "⏱️ Uživatel dostal timeout",
                f"**Uživatel:** {member.mention} ({member.name})\n"
                f"**Doba:** {duration_str}\n"
                f"**Vyprší:** <t:{int(until.timestamp())}:R>",
                discord.Color.orange()
            )

            # Pokusíme se získat záznam z audit logu pro zjištění moderátora a důvodu
            try:
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id and entry.changes.before.timed_out_until != entry.changes.after.timed_out_until:
                        embed.add_field(name="Timeout udělil", value=f"{entry.user.mention} ({entry.user.name})", inline=True)
                        if entry.reason:
                            embed.add_field(name="Důvod", value=entry.reason, inline=True)
                        break
            except (discord.Forbidden, AttributeError):
                pass  # Bot nemá oprávnění číst audit log nebo struktura změn je jiná
        else:
            # Timeout byl zrušen
            embed = self.create_embed(
                "✅ Timeout zrušen",
                f"**Uživatel:** {member.mention} ({member.name})",
                discord.Color.green()
            )

            # Pokusíme se získat záznam z audit logu pro zjištění moderátora
            try:
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                    if entry.target.id == member.id and hasattr(entry.changes, 'before') and hasattr(entry.changes.before, 'timed_out_until'):
                        embed.add_field(name="Timeout zrušil", value=f"{entry.user.mention} ({entry.user.name})", inline=True)
                        if entry.reason:
                            embed.add_field(name="Důvod", value=entry.reason, inline=True)
                        break
            except (discord.Forbidden, AttributeError):
                pass  # Bot nemá oprávnění číst audit log nebo struktura změn je jiná

        embed.set_footer(text=f"ID uživatele: {member.id}")

        await self.send_log(embed)

    @commands.command(name="setupaudit")
    @commands.has_permissions(administrator=True)
    async def setup_audit(self, ctx, channel: discord.TextChannel = None):
        """Nastaví kanál pro audit log (admin only)"""
        if not channel:
            # Pokud není zadán kanál, vytvoříme nový
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
                await ctx.send(f"Vytvořen nový kanál pro audit log: {channel.mention}", ephemeral=True)
            except discord.Forbidden:
                await ctx.send("Nemám oprávnění vytvořit nový kanál.", ephemeral=True)
                return
            except discord.HTTPException as e:
                await ctx.send(f"Nastala chyba při vytváření kanálu: {e}", ephemeral=True)
                return

        # Aktualizujeme .env soubor
        self.update_env_file('AUDIT_LOG_CHANNEL_ID', str(channel.id))

        # Aktualizujeme proměnnou v paměti
        global AUDIT_LOG_CHANNEL_ID
        AUDIT_LOG_CHANNEL_ID = channel.id
        self.audit_channel = channel

        # Odešleme testovací zprávu
        embed = self.create_embed(
            "✅ Audit Log aktivován",
            "Tento kanál byl nastaven jako audit log pro server. Zde se budou zobrazovat záznamy o důležitých událostech na serveru.",
            discord.Color.green()
        )

        await self.send_log(embed)

        await ctx.send(f"Kanál {channel.mention} byl nastaven jako audit log.", ephemeral=True)

    def update_env_file(self, key, value):
        """Aktualizuje hodnotu v konfiguraci"""
        # Check if this is a sensitive key that should be in .env
        sensitive_keys = ['DISCORD_TOKEN', 'YOUTUBE_API_KEY', 'GEMINI_API_KEY', 'OPENROUTER_API_KEY']

        if key in sensitive_keys:
            # Update .env file for sensitive keys
            env_path = '.env'
            try:
                with open(env_path, 'r') as file:
                    lines = file.readlines()

                # Hledáme řádek s daným klíčem
                key_exists = False
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}=") or line.startswith(f"# {key}="):
                        lines[i] = f"{key}={value}\n"
                        key_exists = True
                        break

                # Pokud klíč neexistuje, přidáme ho na konec souboru
                if not key_exists:
                    lines.append(f"{key}={value}\n")

                # Zapíšeme změny zpět do souboru
                with open(env_path, 'w') as file:
                    file.writelines(lines)

                print(f"Hodnota {key} byla aktualizována v .env souboru")
            except Exception as e:
                print(f"Chyba při aktualizaci .env souboru: {e}")
        else:
            # Update config.json for non-sensitive keys
            try:
                import json
                config_path = 'config.json'

                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    config_data = {}

                # Update the value
                config_data[key] = value

                # Save back to config.json
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4)

                print(f"Hodnota {key} byla aktualizována v config.json")
            except Exception as e:
                print(f"Chyba při aktualizaci config.json: {e}")

        # Update the in-memory configuration
        config.set(key, value)

    def get_channel_type(self, channel):
        """Vrátí typ kanálu v čitelné podobě"""
        if isinstance(channel, discord.TextChannel):
            return "Textový kanál"
        elif isinstance(channel, discord.VoiceChannel):
            return "Hlasový kanál"
        elif isinstance(channel, discord.CategoryChannel):
            return "Kategorie"
        elif isinstance(channel, discord.StageChannel):
            return "Pódium"
        elif isinstance(channel, discord.ForumChannel):
            return "Fórum"
        else:
            return "Neznámý typ"

    def format_duration(self, seconds):
        """Formátuje dobu v sekundách do čitelné podoby"""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        parts = []
        if days > 0:
            parts.append(f"{int(days)} {'den' if days == 1 else 'dny' if 2 <= days <= 4 else 'dní'}")
        if hours > 0:
            parts.append(f"{int(hours)} {'hodina' if hours == 1 else 'hodiny' if 2 <= hours <= 4 else 'hodin'}")
        if minutes > 0:
            parts.append(f"{int(minutes)} {'minuta' if minutes == 1 else 'minuty' if 2 <= minutes <= 4 else 'minut'}")
        if seconds > 0 and not parts:  # Sekundy přidáme pouze pokud není nic jiného nebo je to méně než minuta
            parts.append(f"{int(seconds)} {'sekunda' if seconds == 1 else 'sekundy' if 2 <= seconds <= 4 else 'sekund'}")

        return ", ".join(parts) if parts else "0 sekund"

async def setup(bot):
    await bot.add_cog(AuditLog(bot))
