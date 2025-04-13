import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
COUNTING_CHANNEL_ID = int(os.getenv('COUNTING_CHANNEL_ID', 0))
COUNTING_SAVE_FILE = os.getenv('COUNTING_SAVE_FILE', 'db/counting.json')
COUNTING_TOPIC_PREFIX = os.getenv('COUNTING_TOPIC_PREFIX', 'Počítejte od 1 do nekonečna. Další číslo: ')

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        self.bot.loop.create_task(self.update_channel_topic())

    def load_data(self):
        os.makedirs(os.path.dirname(COUNTING_SAVE_FILE), exist_ok=True)

        if not os.path.exists(COUNTING_SAVE_FILE):
            default_data = {
                "current_count": 0,
                "high_score": 0,
                "last_user_id": None,
                "failed_counts": 0,
                "user_stats": {}
            }
            with open(COUNTING_SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)
            return default_data

        try:
            with open(COUNTING_SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if "user_stats" not in data:
                    data["user_stats"] = {}
                return data
        except json.JSONDecodeError:
            return {
                "current_count": 0,
                "high_score": 0,
                "last_user_id": None,
                "failed_counts": 0,
                "user_stats": {}
            }

    def save_data(self):
        with open(COUNTING_SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    async def update_channel_topic(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

        channel = self.bot.get_channel(COUNTING_CHANNEL_ID)
        if not channel:
            print(f"Counting channel with ID {COUNTING_CHANNEL_ID} not found!")
            return

        next_number = self.data["current_count"] + 1
        new_topic = f"{COUNTING_TOPIC_PREFIX}{next_number}"

        try:
            await channel.edit(topic=new_topic)
            print(f"Updated channel topic with next number: {next_number}")
        except discord.Forbidden:
            print("Bot doesn't have permission to edit channel topic")
        except Exception as e:
            print(f"Error updating channel topic: {e}")

    def update_user_stats(self, user_id, username, success=True):
        user_id = str(user_id)

        if user_id not in self.data["user_stats"]:
            self.data["user_stats"][user_id] = {
                "username": username,
                "correct_counts": 0,
                "wrong_counts": 0,
                "last_updated": None
            }

        if success:
            self.data["user_stats"][user_id]["correct_counts"] += 1
        else:
            self.data["user_stats"][user_id]["wrong_counts"] += 1

        self.data["user_stats"][user_id]["last_updated"] = discord.utils.utcnow().isoformat()
        self.data["user_stats"][user_id]["username"] = username

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.channel.id != COUNTING_CHANNEL_ID:
            return


        if message.author.bot:
            return


        is_admin = message.author.guild_permissions.administrator


        try:
            count = int(message.content.strip())
        except ValueError:

            if not is_admin:
                try:

                    await message.delete()


                    try:
                        await message.author.send(f"V kanálu pro počítání jsou povolena pouze čísla. Vaše zpráva byla smazána.")
                    except:

                        await message.channel.send(
                            f"<@{message.author.id}> V tomto kanálu jsou povolena pouze čísla.",
                            delete_after=2
                        )

                except discord.Forbidden:
                    print("Bot doesn't have permission to delete messages")
                except Exception as e:
                    print(f"Error handling non-number message: {e}")
                return
            else:

                return

        expected_count = self.data["current_count"] + 1


        if message.author.id == self.data["last_user_id"]:
            await message.add_reaction("❌")
            await message.channel.send(f"**{message.author.display_name}**, nemůžeš počítat dvakrát za sebou! Počítání začíná znovu od 1.")
            self.data["current_count"] = 0
            self.data["last_user_id"] = None
            self.data["failed_counts"] += 1

            self.update_user_stats(message.author.id, message.author.display_name, success=False)
            self.save_data()
            await self.update_channel_topic()
            return

        if count == expected_count:
            await message.add_reaction("✅")
            self.data["current_count"] = count
            self.data["last_user_id"] = message.author.id

            self.update_user_stats(message.author.id, message.author.display_name, success=True)

            if count > self.data["high_score"]:
                self.data["high_score"] = count
                if count % 10 == 0:
                    await message.channel.send(f"🎉 Nový rekord: **{count}**! Gratulujeme!")

            if count % 100 == 0:
                await message.channel.send(f"🎊 **Dosáhli jste {count}!** Skvělá práce!")

            self.save_data()
            await self.update_channel_topic()
        else:
            await message.add_reaction("❌")
            await message.channel.send(f"**{message.author.display_name}** pokazil počítání na **{count}**! Správné číslo bylo **{expected_count}**. Počítání začíná znovu od 1.")
            self.data["current_count"] = 0
            self.data["last_user_id"] = None
            self.data["failed_counts"] += 1
            self.update_user_stats(message.author.id, message.author.display_name, success=False)
            self.save_data()
            await self.update_channel_topic()

    @commands.command(name="count")
    async def count_status(self, ctx):
        """Show the current counting status"""
        embed = discord.Embed(
            title="Počítání",
            description=f"Aktuální stav počítání v <#{COUNTING_CHANNEL_ID}>",
            color=discord.Color.blue()
        )

        embed.add_field(name="Aktuální číslo", value=str(self.data["current_count"]), inline=True)
        embed.add_field(name="Další číslo", value=str(self.data["current_count"] + 1), inline=True)
        embed.add_field(name="Rekord", value=str(self.data["high_score"]), inline=True)
        embed.add_field(name="Počet selhání", value=str(self.data["failed_counts"]), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="countreset")
    @commands.has_permissions(administrator=True)
    async def reset_count(self, ctx):
        """Reset the counting (admin only)"""
        self.data["current_count"] = 0
        self.data["last_user_id"] = None
        self.save_data()
        await self.update_channel_topic()

        await ctx.send("Počítání bylo resetováno na 0.")

    @commands.command(name="countrules")
    async def count_rules(self, ctx):
        """Show the counting rules"""
        embed = discord.Embed(
            title="Pravidla počítání",
            description="Jak funguje počítání v tomto serveru:",
            color=discord.Color.gold()
        )

        rules = [
            "Počítejte od 1 do nekonečna, každé číslo musí být o 1 větší než předchozí",
            "Jeden člověk nemůže počítat dvakrát za sebou (je potřeba alespoň dva účastníky)",
            "Pokud někdo napíše špatné číslo, počítání se resetuje na 0",
            "V kanálu jsou povolena pouze čísla, ostatní zprávy budou smazány (kromě adminů)",
            "Žádné podvádění nebo používání botů k počítání"
        ]

        for i, rule in enumerate(rules, 1):
            embed.add_field(name=f"Pravidlo {i}", value=rule, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="countstats")
    async def count_stats(self, ctx):
        """Show counting statistics for top 10 users"""
        if not self.data["user_stats"]:
            await ctx.send("Zatím nejsou k dispozici žádné statistiky počítání.")
            return

        # Sort users by correct counts (descending)
        sorted_users = sorted(
            self.data["user_stats"].items(),
            key=lambda x: x[1]["correct_counts"],
            reverse=True
        )

        # Take top 10
        top_users = sorted_users[:10]

        embed = discord.Embed(
            title="📊 Statistiky počítání",
            description=f"Nejlepších 10 počítačů | Rekord: **{self.data['high_score']}**",
            color=discord.Color.blue()
        )

        for i, (user_id, stats) in enumerate(top_users, 1):
            username = stats["username"]
            correct = stats["correct_counts"]
            wrong = stats["wrong_counts"]
            total = correct + wrong
            accuracy = (correct / total * 100) if total > 0 else 0

            value = f"**Správné počty:** {correct}\n"
            value += f"**Chybné počty:** {wrong}\n"
            value += f"**Přesnost:** {accuracy:.1f}%"

            embed.add_field(
                name=f"{i}. {username}",
                value=value,
                inline=True
            )

            # Add empty field every 2 entries for better formatting
            if i % 2 == 0 and i < len(top_users):
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        embed.set_footer(text=f"Celkem počet selhání: {self.data['failed_counts']}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Counting(bot))
