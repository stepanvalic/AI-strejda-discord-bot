import discord
from discord.ext import commands
from utils import config

WELCOME_CHANNEL_ID = config.get_int('WELCOME_CHANNEL_ID')
DEFAULT_ROLE_ID = config.get_int('DEFAULT_ROLE_ID')

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)

        if not welcome_channel:
            print(f"Welcome channel with ID {WELCOME_CHANNEL_ID} not found!")
            return

        # Přidělení defaultní role, pokud je nastavena
        if DEFAULT_ROLE_ID != 0:
            try:
                # Získání role podle ID
                default_role = member.guild.get_role(DEFAULT_ROLE_ID)

                if default_role:
                    await member.add_roles(default_role)
                    print(f"Přidělena defaultní role '{default_role.name}' uživateli {member.display_name}")
                else:
                    print(f"Defaultní role s ID {DEFAULT_ROLE_ID} nebyla nalezena!")
            except discord.Forbidden:
                print(f"Bot nemá oprávnění přidělit roli uživateli {member.display_name}")
            except Exception as e:
                print(f"Chyba při přidělování defaultní role uživateli {member.display_name}: {str(e)}")

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

        # Přidělení defaultní role, pokud je nastavena
        role_added = False
        if DEFAULT_ROLE_ID != 0:
            try:
                # Získání role podle ID
                default_role = ctx.guild.get_role(DEFAULT_ROLE_ID)

                if default_role:
                    # Kontrola, zda uživatel již roli nemá
                    if default_role not in member.roles:
                        await member.add_roles(default_role)
                        role_added = True
                        print(f"Přidělena defaultní role '{default_role.name}' uživateli {member.display_name} pomocí příkazu !welcome")
                else:
                    print(f"Defaultní role s ID {DEFAULT_ROLE_ID} nebyla nalezena!")
            except discord.Forbidden:
                print(f"Bot nemá oprávnění přidělit roli uživateli {member.display_name}")
            except Exception as e:
                print(f"Chyba při přidělování defaultní role uživateli {member.display_name}: {str(e)}")

        await self.on_member_join(member)

        if role_added:
            await ctx.send(f"Sent welcome message for {member.display_name} and assigned default role!")
        else:
            await ctx.send(f"Sent welcome message for {member.display_name}!")

    @commands.command(name="chack-all-default-role")
    @commands.has_permissions(administrator=True)
    async def check_roles(self, ctx):
        """Zkontroluje všechny uživatele a přidělí jim defaultní roli, pokud ji nemají"""
        if DEFAULT_ROLE_ID == 0:
            await ctx.send("Defaultní role není nastavena v konfiguraci!")
            return

        # Získání role podle ID
        default_role = ctx.guild.get_role(DEFAULT_ROLE_ID)
        if not default_role:
            await ctx.send(f"Defaultní role s ID {DEFAULT_ROLE_ID} nebyla nalezena!")
            return

        # Informační zpráva o začátku kontroly
        status_message = await ctx.send(f"Kontroluji všechny uživatele a přiděluji roli {default_role.mention}...")

        # Počítadla pro statistiky
        total_members = 0
        roles_added = 0
        errors = 0

        # Kontrola všech členů serveru
        for member in ctx.guild.members:
            total_members += 1

            # Přeskočit boty
            if member.bot:
                continue

            # Kontrola, zda uživatel již roli nemá
            if default_role not in member.roles:
                try:
                    await member.add_roles(default_role)
                    roles_added += 1
                    print(f"Přidělena defaultní role '{default_role.name}' uživateli {member.display_name}")
                except Exception as e:
                    errors += 1
                    print(f"Chyba při přidělování defaultní role uživateli {member.display_name}: {str(e)}")

        # Aktualizace zprávy s výsledky
        embed = discord.Embed(
            title="✅ Kontrola rolí dokončena",
            description=f"Role {default_role.mention} byla zkontrolována u všech uživatelů.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Statistiky",
            value=f"Celkem uživatelů: **{total_members}**\n"
                  f"Přiděleno rolí: **{roles_added}**\n"
                  f"Chyby: **{errors}**"
        )

        await status_message.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
