import discord
from discord.ext import commands
import datetime
import re

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time_str):
        """Parse time string in format like '5s', '3m', '2h', '1d', '1y' or combinations like '1d12h30m'"""
        if not time_str:
            return datetime.timedelta(minutes=5), False  # Default 5 minutes, not capped

        # If it's just a number, treat it as minutes
        if time_str.isdigit():
            minutes = int(time_str)
            return datetime.timedelta(minutes=minutes), False

        total_seconds = 0
        time_units = {
            's': 1,               # seconds
            'm': 60,              # minutes
            'h': 3600,            # hours
            'd': 86400,           # days
            'y': 31536000         # years (365 days)
        }

        # Find all time specifications like '5s', '3m', etc.
        pattern = r'(\d+)([smhdy])'
        matches = re.findall(pattern, time_str)

        if not matches:
            # If no valid format found, default to 5 minutes
            return datetime.timedelta(minutes=5), False

        for value, unit in matches:
            total_seconds += int(value) * time_units[unit]

        # Discord's maximum timeout duration is 28 days
        max_timeout_seconds = 28 * 24 * 60 * 60  # 28 days in seconds
        was_capped = False

        if total_seconds > max_timeout_seconds:
            total_seconds = max_timeout_seconds
            was_capped = True

        return datetime.timedelta(seconds=total_seconds), was_capped

    def format_time_duration(self, delta):
        """Format timedelta to human readable string"""
        seconds = int(delta.total_seconds())
        periods = [
            ('rok', 'roky', 'let', 60*60*24*365),
            ('den', 'dny', 'dní', 60*60*24),
            ('hodina', 'hodiny', 'hodin', 60*60),
            ('minuta', 'minuty', 'minut', 60),
            ('sekunda', 'sekundy', 'sekund', 1)
        ]

        parts = []
        for singular, dual, plural, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                if period_value == 1:
                    parts.append(f"{period_value} {singular}")
                elif 2 <= period_value <= 4:
                    parts.append(f"{period_value} {dual}")
                else:
                    parts.append(f"{period_value} {plural}")

        return ', '.join(parts) if parts else "0 sekund"

    @commands.command(name="timeout")
    @commands.has_permissions(administrator=True)
    async def timeout_user(self, ctx, member: discord.Member, *, time_str=None):
        """Dá uživateli timeout na určitou dobu (admin only)
        Formát času: 5s, 3m, 2h, 1d, 1y nebo kombinace např. 1d12h30m
        Maximum je 28 dní (Discord limit)"""
        if member.guild_permissions.administrator:
            await ctx.send(f"Nemůžeš dát timeout administrátorovi.", ephemeral=True)
            return

        # Parse time string to timedelta
        duration, was_capped = self.parse_time(time_str)
        human_readable_duration = self.format_time_duration(duration)

        try:
            # Calculate end time
            end_time = datetime.datetime.now(datetime.timezone.utc) + duration
            discord_timestamp = f"<t:{int(end_time.timestamp())}:R>"

            # Apply timeout
            await member.timeout(duration, reason=f"Timeout zadán administrátorem {ctx.author.display_name}")

            # Create embed for confirmation
            embed = discord.Embed(
                title="⏱️ Timeout udělen",
                description=f"Uživatel {member.mention} dostal timeout na **{human_readable_duration}**.",
                color=discord.Color.orange()
            )

            embed.add_field(name="Konec timeoutu", value=f"Timeout vyprší {discord_timestamp} ({human_readable_duration})", inline=False)

            # Add note about capping if needed
            if was_capped:
                embed.add_field(name="Poznámka", value="Zadaná doba překročila maximální povolenou délku timeoutu (28 dní). Timeout byl automaticky omezen na 28 dní.", inline=False)

            embed.set_footer(text=f"Timeout zadal: {ctx.author.display_name}")
            embed.timestamp = datetime.datetime.now()

            await ctx.send(embed=embed, ephemeral=True)

            # Notify the user
            try:
                user_embed = discord.Embed(
                    title="⏱️ Dostal jsi timeout",
                    description=f"Administrátor ti udělil timeout na **{human_readable_duration}**.",
                    color=discord.Color.red()
                )
                user_embed.add_field(name="Konec timeoutu", value=f"Timeout vyprší {discord_timestamp} ({human_readable_duration})", inline=False)
                user_embed.set_footer(text=f"Timeout zadal: {ctx.author.display_name}")
                user_embed.timestamp = datetime.datetime.now()

                await member.send(embed=user_embed)
            except discord.Forbidden:
                # User has DMs disabled
                pass

        except discord.Forbidden:
            await ctx.send("Nemám dostatečná oprávnění k udělení timeoutu.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Nastala chyba při udělování timeoutu: {str(e)}", ephemeral=True)

    @commands.command(name="untimeout", aliases=["unmute"])
    @commands.has_permissions(administrator=True)
    async def remove_timeout(self, ctx, member: discord.Member):
        """Zruší timeout uživateli (admin only)"""
        try:
            # Remove timeout by setting it to None
            await member.timeout(None, reason=f"Timeout zrušen administrátorem {ctx.author.display_name}")

            # Create embed for confirmation
            embed = discord.Embed(
                title="✅ Timeout zrušen",
                description=f"Uživateli {member.mention} byl zrušen timeout.",
                color=discord.Color.green()
            )

            embed.set_footer(text=f"Timeout zrušil: {ctx.author.display_name}")
            embed.timestamp = datetime.datetime.now()

            await ctx.send(embed=embed, ephemeral=True)

            # Notify the user
            try:
                user_embed = discord.Embed(
                    title="✅ Timeout zrušen",
                    description=f"Administrátor ti zrušil timeout. Nyní můžeš opět komunikovat na serveru.",
                    color=discord.Color.green()
                )
                user_embed.set_footer(text=f"Timeout zrušil: {ctx.author.display_name}")
                user_embed.timestamp = datetime.datetime.now()

                await member.send(embed=user_embed)
            except discord.Forbidden:
                # User has DMs disabled
                pass

        except discord.Forbidden:
            await ctx.send("Nemám dostatečná oprávnění ke zrušení timeoutu.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Nastala chyba při rušení timeoutu: {str(e)}", ephemeral=True)

    @commands.command(name="ban")
    @commands.has_permissions(administrator=True)
    async def ban_user(self, ctx, member: discord.Member, *, reason=None):
        """Zabanuje uživatele natrvalo (admin only)"""
        if member.guild_permissions.administrator:
            await ctx.send(f"Nemůžeš zabanovat administrátora.", ephemeral=True)
            return

        try:
            # Prepare ban reason
            ban_reason = reason if reason else f"Zabanován administrátorem {ctx.author.display_name}"

            # Create embed for confirmation
            embed = discord.Embed(
                title="🔨 Uživatel zabanován",
                description=f"Uživatel {member.mention} byl trvale zabanován.",
                color=discord.Color.red()
            )

            if reason:
                embed.add_field(name="Důvod", value=reason, inline=False)

            embed.set_footer(text=f"Ban zadal: {ctx.author.display_name}")
            embed.timestamp = datetime.datetime.now()

            # Try to notify the user before banning
            try:
                user_embed = discord.Embed(
                    title="🔨 Byl jsi zabanován",
                    description=f"Byl jsi trvale zabanován ze serveru.",
                    color=discord.Color.red()
                )

                if reason:
                    user_embed.add_field(name="Důvod", value=reason, inline=False)

                user_embed.set_footer(text=f"Ban zadal: {ctx.author.display_name}")
                user_embed.timestamp = datetime.datetime.now()

                await member.send(embed=user_embed)
            except discord.Forbidden:
                # User has DMs disabled
                pass

            # Ban the user
            await member.ban(reason=ban_reason)
            await ctx.send(embed=embed, ephemeral=True)

        except discord.Forbidden:
            await ctx.send("Nemám dostatečná oprávnění k zabanování uživatele.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Nastala chyba při banování uživatele: {str(e)}", ephemeral=True)

    @commands.command(name="unban")
    @commands.has_permissions(administrator=True)
    async def unban_user(self, ctx, user_id: str):
        """Odbanuje uživatele podle ID (admin only)"""
        try:
            # Try to convert the user_id to an integer
            try:
                user_id = int(user_id)
            except ValueError:
                await ctx.send("Neplatné ID uživatele. Zadej platné číselné ID.", ephemeral=True)
                return

            # Get the user
            user = discord.Object(id=user_id)

            # Unban the user
            await ctx.guild.unban(user, reason=f"Odbanován administrátorem {ctx.author.display_name}")

            # Create embed for confirmation
            embed = discord.Embed(
                title="✅ Uživatel odbanován",
                description=f"Uživatel s ID `{user_id}` byl odbanován.",
                color=discord.Color.green()
            )

            embed.set_footer(text=f"Unban zadal: {ctx.author.display_name}")
            embed.timestamp = datetime.datetime.now()

            await ctx.send(embed=embed, ephemeral=True)

        except discord.NotFound:
            await ctx.send(f"Uživatel s ID `{user_id}` nebyl nalezen mezi zabanovanými uživateli.", ephemeral=True)
        except discord.Forbidden:
            await ctx.send("Nemám dostatečná oprávnění k odbanování uživatele.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Nastala chyba při odbanování uživatele: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
