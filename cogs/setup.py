import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

            embed = discord.Embed(
                title="✅ YouTube kanál vytvořen",
                description=f"Kanál {channel.mention} byl úspěšně vytvořen a nastaven pro YouTube oznámení.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="Nastavení",
                value=f"ID kanálu: `{channel.id}`\nPřidejte toto ID do vašeho .env souboru jako YOUTUBE_NOTIFICATION_CHANNEL_ID."
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

            embed = discord.Embed(
                title="✅ Counting kanál vytvořen",
                description=f"Kanál {channel.mention} byl úspěšně vytvořen a nastaven pro hru na počítání.",
                color=discord.Color.green()
            )

            embed.add_field(
                name="Nastavení",
                value=f"ID kanálu: `{channel.id}`\nPřidejte toto ID do vašeho .env souboru jako COUNTING_CHANNEL_ID."
            )

            await ctx.send(embed=embed, ephemeral=True)

        except Exception as e:
            await ctx.send(f"Chyba při vytváření counting kanálu: {str(e)}", ephemeral=True)

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup_all(self, ctx):
        await self.setup_youtube(ctx)
        await self.setup_counting(ctx)

        embed = discord.Embed(
            title="⚠️ Nastavení dokončeno",
            description="Všechny kanály byly úspěšně vytvořeny, ale je potřeba je ručně nastavit v .env souboru.",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="⚠️ DŮLEŽITÉ UPOZORNĚNÍ",
            value="Příkaz setup je na vlastní nebezpečí! Nezapomeňte ručně nastavit ID kanálů v .env souboru.\n\n"
                  "Nezapomeňte nastavit následující proměnné v .env souboru:\n"
                  "- DISCORD_TOKEN\n"
                  "- GUILD_ID\n"
                  "- WELCOME_CHANNEL_ID\n"
                  "- YOUTUBE_API_KEY\n"
                  "- YOUTUBE_CHANNEL_ID\n"
                  "- YOUTUBE_NOTIFICATION_CHANNEL_ID\n"
                  "- COUNTING_CHANNEL_ID"
        )

        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
