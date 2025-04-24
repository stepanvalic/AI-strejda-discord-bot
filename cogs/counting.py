import os
import json
import discord
from discord.ext import commands
import config

# Get configuration from config.py
COUNTING_CHANNEL_ID = config.COUNTING_CHANNEL_ID
COUNTING_SAVE_FILE = config.COUNTING_SAVE_FILE
COUNTING_TOPIC_PREFIX = config.COUNTING_TOPIC_PREFIX

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

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
        # Funkce je prázdná, protože Discord blokuje časté aktualizace tématu kanálu
        # a není potřeba ji používat
        pass

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
        else:
            await message.add_reaction("❌")
            await message.channel.send(f"**{message.author.display_name}** pokazil počítání na **{count}**! Správné číslo bylo **{expected_count}**. Počítání začíná znovu od 1.")
            self.data["current_count"] = 0
            self.data["last_user_id"] = None
            self.data["failed_counts"] += 1
            self.update_user_stats(message.author.id, message.author.display_name, success=False)
            self.save_data()

    @commands.command(name="count")
    @commands.has_permissions(administrator=True)
    async def count_status(self, ctx):
        """Show the current counting status (admin only)"""
        # Kontrola, zda je příkaz použit v kanálu pro počítání
        if ctx.channel.id != COUNTING_CHANNEL_ID:
            try:
                await ctx.message.delete()
                await ctx.author.send(f"Příkaz !count lze použít pouze v kanálu pro počítání <#{COUNTING_CHANNEL_ID}>")
            except Exception as e:
                print(f"Chyba při mazání zprávy nebo posílání DM: {str(e)}")
            return

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

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
        # Kontrola, zda je příkaz použit v kanálu pro počítání
        if ctx.channel.id != COUNTING_CHANNEL_ID:
            try:
                await ctx.message.delete()
                await ctx.author.send(f"Příkaz !countreset lze použít pouze v kanálu pro počítání <#{COUNTING_CHANNEL_ID}>")
            except Exception as e:
                print(f"Chyba při mazání zprávy nebo posílání DM: {str(e)}")
            return

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        self.data["current_count"] = 0
        self.data["last_user_id"] = None
        self.save_data()

        await ctx.send("Počítání bylo resetováno na 0.")

    @commands.command(name="countrules")
    async def count_rules(self, ctx):
        """Show the counting rules"""
        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

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

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Handle message edits in the counting channel"""
        # Ignore if not in counting channel
        if before.channel.id != COUNTING_CHANNEL_ID:
            return

        # Ignore bot messages
        if before.author.bot:
            return

        # Ignore if content didn't change
        if before.content == after.content:
            return

        # Check if the original message was a valid number
        try:
            original_number = int(before.content.strip())
        except ValueError:
            return  # Original message wasn't a number, ignore

        # Check if the edited message is still a number
        try:
            new_number = int(after.content.strip())
        except ValueError:
            # If edited to non-number, delete it
            await after.delete()
            return

        # If the number was changed, handle it
        if original_number != new_number:
            # Delete the edited message
            await after.delete()

            # Send a notification about the edit
            await before.channel.send(
                f"**{before.author.display_name}** upravil zprávu z **{original_number}** na **{new_number}**. "
                f"Úpravy čísel nejsou povoleny."
            )

            # Create a webhook to send a message as the original user
            try:
                # Create a webhook in the channel
                webhook = await before.channel.create_webhook(name="CountingHelper")

                # Send the original number as the user
                await webhook.send(
                    content=str(original_number),
                    username=before.author.display_name,
                    avatar_url=before.author.display_avatar.url
                )

                # Delete the webhook after use
                await webhook.delete()
            except discord.Forbidden:
                # If we don't have permission to create webhooks, just send the message normally
                await before.channel.send(
                    f"**{before.author.display_name}**: {original_number}"
                )

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
