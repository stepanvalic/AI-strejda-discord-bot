import os
import json
import discord
import asyncio
import datetime
from discord.ext import commands
from utils import config

COUNTING_CHANNEL_ID = config.get_int('COUNTING_CHANNEL_ID')
COUNTING_SAVE_FILE = config.get('COUNTING_SAVE_FILE', 'db/counting.json')
COUNTING_TOPIC_PREFIX = config.get('COUNTING_TOPIC_PREFIX', 'Počítejte od 1 do nekonečna. Další číslo: ')

# Konstanty pro blokování uživatelů
FIRST_BAN_THRESHOLD = 5  # Počet chyb, po kterých bude uživatel poprvé zablokován
FIRST_BAN_DURATION = 1   # Doba prvního blokování ve dnech
SECOND_BAN_THRESHOLD = 2  # Počet chyb po odblokování, po kterých bude uživatel znovu zablokován
SECOND_BAN_DURATION = 3   # Doba druhého blokování ve dnech

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        self.message_cache = {}  # Cache pro sledování zpráv v kanálu počítání

    def load_data(self):
        os.makedirs(os.path.dirname(COUNTING_SAVE_FILE), exist_ok=True)

        if not os.path.exists(COUNTING_SAVE_FILE):
            default_data = {
                "current_count": 0,
                "high_score": 0,
                "last_user_id": None,
                "failed_counts": 0,
                "user_stats": {},
                "blocked_users": {}
            }
            with open(COUNTING_SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)
            return default_data

        try:
            with open(COUNTING_SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

                if "user_stats" not in data:
                    data["user_stats"] = {}
                if "blocked_users" not in data:
                    data["blocked_users"] = {}
                return data
        except json.JSONDecodeError:
            return {
                "current_count": 0,
                "high_score": 0,
                "last_user_id": None,
                "failed_counts": 0,
                "user_stats": {},
                "blocked_users": {}
            }

    def save_data(self):
        with open(COUNTING_SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    async def update_channel_topic(self):
        # Funkce je prázdná, protože Discord blokuje časté aktualizace tématu kanálu
        # a není potřeba ji používat
        pass

    def clean_message_cache(self, max_size=100):
        """Vyčistí cache zpráv, pokud je příliš velká"""
        if len(self.message_cache) > max_size:
            # Seřadíme klíče podle ID zprávy (novější zprávy mají vyšší ID)
            sorted_keys = sorted(self.message_cache.keys())
            # Odstraníme nejstarší zprávy, aby zůstalo pouze max_size zpráv
            keys_to_remove = sorted_keys[:-max_size]
            for key in keys_to_remove:
                del self.message_cache[key]

    def update_user_stats(self, user_id, username, success=True):
        user_id = str(user_id)

        if user_id not in self.data["user_stats"]:
            self.data["user_stats"][user_id] = {
                "username": username,
                "correct_counts": 0,
                "wrong_counts": 0,
                "last_updated": None,
                "consecutive_fails": 0,
                "total_blocks": 0
            }

        if success:
            self.data["user_stats"][user_id]["correct_counts"] += 1
            # Resetujeme počet po sobě jdoucích chyb při úspěchu
            self.data["user_stats"][user_id]["consecutive_fails"] = 0
        else:
            self.data["user_stats"][user_id]["wrong_counts"] += 1
            # Zvýšíme počet po sobě jdoucích chyb
            self.data["user_stats"][user_id]["consecutive_fails"] += 1

        self.data["user_stats"][user_id]["last_updated"] = discord.utils.utcnow().isoformat()
        self.data["user_stats"][user_id]["username"] = username

    async def block_user(self, user_id, user, _, duration_days):
        """Zablokuje uživatele od psaní do kanálu počítání na určitou dobu

        Parametry:
            user_id: ID uživatele
            user: Objekt uživatele
            _: Nepoužívaný parametr (pro kompatibilitu)
            duration_days: Doba blokace ve dnech
        """
        user_id = str(user_id)

        # Vytvoření override pro kanál, který zakáže uživateli posílat zprávy
        try:
            # Získání objektu kanálu
            channel_obj = self.bot.get_channel(COUNTING_CHANNEL_ID)
            if not channel_obj:
                print(f"Kanál s ID {COUNTING_CHANNEL_ID} nebyl nalezen")
                return False

            # Vytvoření override pro uživatele
            perms = discord.PermissionOverwrite()
            perms.send_messages = False
            await channel_obj.set_permissions(user, overwrite=perms)

            # Uložení informací o blokaci
            end_time = datetime.datetime.now() + datetime.timedelta(days=duration_days)

            self.data["blocked_users"][user_id] = {
                "username": user.display_name,
                "blocked_at": datetime.datetime.now().isoformat(),
                "end_time": end_time.isoformat(),
                "duration_days": duration_days
            }

            # Zvýšení počtu blokací pro uživatele
            if user_id in self.data["user_stats"]:
                self.data["user_stats"][user_id]["total_blocks"] += 1

            self.save_data()

            # Naplánování odblokování
            self.bot.loop.create_task(self.schedule_unblock(user_id, user, channel_obj, end_time))

            return True
        except Exception as e:
            print(f"Chyba při blokování uživatele {user.display_name}: {e}")
            return False

    async def unblock_user(self, user_id, user, channel):
        """Odblokuje uživatele od psaní do kanálu počítání"""
        user_id = str(user_id)

        try:
            # Odstranění override pro uživatele
            await channel.set_permissions(user, overwrite=None)

            # Odstranění záznamu o blokaci
            if user_id in self.data["blocked_users"]:
                del self.data["blocked_users"][user_id]
                self.save_data()

            return True
        except Exception as e:
            print(f"Chyba při odblokování uživatele {user.display_name}: {e}")
            return False

    async def schedule_unblock(self, user_id, user, channel, end_time):
        """Naplánuje odblokování uživatele v určitý čas"""
        user_id = str(user_id)

        # Výpočet doby do odblokování
        now = datetime.datetime.now()
        if isinstance(end_time, str):
            end_time = datetime.datetime.fromisoformat(end_time)

        time_delta = (end_time - now).total_seconds()

        if time_delta > 0:
            # Počkáme do konce blokace
            await asyncio.sleep(time_delta)

            # Kontrola, zda uživatel je stále blokován (mohl být odblokován ručně)
            if user_id in self.data["blocked_users"]:
                # Odblokování uživatele
                success = await self.unblock_user(user_id, user, channel)

                if success:
                    # Informování uživatele o odblokování
                    try:
                        await user.send(f"Byl jsi odblokován v kanálu pro počítání. Nyní můžeš opět počítat, ale buď opatrný - pokud uděláš další chyby, budeš zablokován na delší dobu.")
                    except:
                        print(f"Nepodařilo se poslat zprávu o odblokování uživateli {user.display_name}")

    async def check_and_restore_blocks(self):
        """Kontroluje a obnovuje blokace uživatelů po restartu bota"""
        # Získání objektu kanálu
        channel = self.bot.get_channel(COUNTING_CHANNEL_ID)
        if not channel:
            print(f"Kanál s ID {COUNTING_CHANNEL_ID} nebyl nalezen")
            return

        # Procházení všech blokovaných uživatelů
        for user_id, block_data in list(self.data["blocked_users"].items()):
            try:
                # Získání objektu uživatele
                user = await self.bot.fetch_user(int(user_id))
                if not user:
                    print(f"Uživatel s ID {user_id} nebyl nalezen")
                    continue

                # Kontrola, zda blokace již nevypršela
                end_time = datetime.datetime.fromisoformat(block_data["end_time"])
                now = datetime.datetime.now()

                if end_time > now:
                    # Blokace ještě nevypršela, obnovíme ji
                    perms = discord.PermissionOverwrite()
                    perms.send_messages = False
                    await channel.set_permissions(user, overwrite=perms)

                    # Naplánování odblokování
                    self.bot.loop.create_task(self.schedule_unblock(user_id, user, channel, end_time))

                    print(f"Obnovena blokace pro uživatele {user.display_name} do {end_time}")
                else:
                    # Blokace již vypršela, odstraníme ji
                    await self.unblock_user(user_id, user, channel)
                    print(f"Odstraněna vypršená blokace pro uživatele {user.display_name}")
            except Exception as e:
                print(f"Chyba při obnovování blokace pro uživatele {user_id}: {e}")

    def is_user_blocked(self, user_id):
        """Kontroluje, zda je uživatel blokován"""
        user_id = str(user_id)
        return user_id in self.data["blocked_users"]

    async def check_and_block_user(self, user_id, user, channel):
        """Kontroluje, zda by měl být uživatel zablokován na základě počtu chyb"""
        user_id = str(user_id)

        if user_id not in self.data["user_stats"]:
            return False

        # Získání statistik uživatele
        stats = self.data["user_stats"][user_id]
        consecutive_fails = stats.get("consecutive_fails", 0)
        total_blocks = stats.get("total_blocks", 0)

        # Kontrola, zda by měl být uživatel zablokován
        if consecutive_fails >= FIRST_BAN_THRESHOLD and total_blocks == 0:
            # První blokace
            duration = FIRST_BAN_DURATION
            await self.block_user(user_id, user, channel, duration)

            # Informování uživatele
            try:
                await user.send(
                    f"Byl jsi zablokován v kanálu pro počítání na {duration} {'den' if duration == 1 else 'dny'} "
                    f"protože jsi pokazil počítání {consecutive_fails}x. "
                    f"Po odblokování buď opatrný, pokud pokazíš počítání znovu {SECOND_BAN_THRESHOLD}x, "
                    f"budeš zablokován na {SECOND_BAN_DURATION} dny."
                )
            except:
                # Pokud nelze poslat DM, pošleme zprávu do kanálu
                await channel.send(
                    f"**{user.display_name}** byl zablokován v tomto kanálu na {duration} {'den' if duration == 1 else 'dny'} "
                    f"za opakované pokazení počítání ({consecutive_fails}x)."
                )

            return True

        elif consecutive_fails >= SECOND_BAN_THRESHOLD and total_blocks > 0:
            # Opakovaná blokace
            duration = SECOND_BAN_DURATION
            await self.block_user(user_id, user, channel, duration)

            # Informování uživatele
            try:
                await user.send(
                    f"Byl jsi znovu zablokován v kanálu pro počítání, tentokrát na {duration} dny, "
                    f"protože jsi opět pokazil počítání {consecutive_fails}x po předchozí blokaci."
                )
            except:
                # Pokud nelze poslat DM, pošleme zprávu do kanálu
                await channel.send(
                    f"**{user.display_name}** byl znovu zablokován v tomto kanálu na {duration} dny "
                    f"za opakované pokazení počítání po předchozí blokaci."
                )

            return True

        return False

    @commands.Cog.listener()
    async def on_ready(self):
        """Inicializace po připravení bota"""
        print(f"Counting cog připraven, obnovuji blokace uživatelů...")
        await self.check_and_restore_blocks()
        print(f"Blokace uživatelů obnoveny")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != COUNTING_CHANNEL_ID:
            return

        if message.author.bot:
            return

        is_admin = message.author.guild_permissions.administrator

        # Kontrola, zda je uživatel blokován (admini mohou psát vždy)
        if not is_admin and self.is_user_blocked(message.author.id):
            try:
                # Smazání zprávy od blokovaného uživatele
                await message.delete()

                # Informování uživatele o blokaci (pouze jednou za 10 minut)
                user_id = str(message.author.id)
                block_data = self.data["blocked_users"].get(user_id, {})
                last_notification = block_data.get("last_notification")
                now = datetime.datetime.now().isoformat()

                if not last_notification or (datetime.datetime.fromisoformat(now) - datetime.datetime.fromisoformat(last_notification)).total_seconds() > 600:
                    try:
                        end_time = datetime.datetime.fromisoformat(block_data.get("end_time", now))
                        time_left = end_time - datetime.datetime.now()
                        days = time_left.days
                        hours = time_left.seconds // 3600
                        minutes = (time_left.seconds % 3600) // 60

                        time_str = ""
                        if days > 0:
                            time_str += f"{days} {'den' if days == 1 else 'dny' if days < 5 else 'dní'} "
                        if hours > 0:
                            time_str += f"{hours} {'hodinu' if hours == 1 else 'hodiny' if hours < 5 else 'hodin'} "
                        if minutes > 0 and days == 0:
                            time_str += f"{minutes} {'minutu' if minutes == 1 else 'minuty' if minutes < 5 else 'minut'}"

                        await message.author.send(
                            f"Jsi zablokován v kanálu pro počítání. "
                            f"Blokace vyprší za {time_str.strip()}."
                        )

                        # Aktualizace času poslední notifikace
                        block_data["last_notification"] = now
                        self.data["blocked_users"][user_id] = block_data
                        self.save_data()
                    except:
                        pass
            except:
                pass
            return

        try:
            count = int(message.content.strip(), 0)
        except ValueError:
            if not is_admin:
                try:
                    await message.delete()

                    try:
                        await message.author.send(f"V kanálu pro počítání jsou povolena pouze čísla. Vaše zpráva byla smazána.")
                    except:
                        # Získání nebo vytvoření webhooků
                        webhook = await self.get_or_create_webhook(message.channel)

                        if webhook:
                            # Pošleme zprávu přes webhook
                            await webhook.send(
                                content=f"V tomto kanálu jsou povolena pouze čísla.",
                                username=message.author.display_name,
                                avatar_url=message.author.display_avatar.url
                            )
                        else:
                            # Fallback na normální zprávu
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

            # Kontrola, zda by měl být uživatel zablokován
            if not is_admin:
                await self.check_and_block_user(message.author.id, message.author, message.channel)

            return

        if count == expected_count:
            await message.add_reaction("✅")
            self.data["current_count"] = count
            self.data["last_user_id"] = message.author.id

            # Uložení zprávy do cache
            self.message_cache[message.id] = {
                "content": message.content,
                "author_id": message.author.id,
                "author_name": message.author.display_name,
                "count": count
            }

            # Vyčištění cache, pokud je příliš velká
            self.clean_message_cache()

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

            # Kontrola, zda by měl být uživatel zablokován
            if not is_admin:
                await self.check_and_block_user(message.author.id, message.author, message.channel)

    async def get_or_create_webhook(self, channel):
        """Získá nebo vytvoří webhook pro daný kanál"""
        # Nejprve zkusíme najít existující webhook
        webhooks = await channel.webhooks()
        for webhook in webhooks:
            if webhook.name == "CountingHelper":
                return webhook

        # Pokud webhook neexistuje, vytvoříme nový
        try:
            return await channel.create_webhook(name="CountingHelper")
        except discord.Forbidden:
            print("Bot doesn't have permission to create webhooks")
            return None
        except Exception as e:
            print(f"Error creating webhook: {e}")
            return None

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Sleduje úpravy zpráv v kanálu počítání"""
        # Kontrola, zda je zpráva z kanálu počítání
        if before.channel.id != COUNTING_CHANNEL_ID:
            return

        # Ignorujeme zprávy od botů
        if before.author.bot:
            return

        # Ignorujeme, pokud se obsah nezměnil
        if before.content == after.content:
            return

        # Kontrola, zda je zpráva v cache a zda je to poslední platné číslo
        if before.id in self.message_cache and self.message_cache[before.id]["count"] == self.data["current_count"]:
            cached_message = self.message_cache[before.id]
            count = cached_message["count"]
            author_name = cached_message["author_name"]
            author_id = cached_message["author_id"]

            try:
                # Smazání upravené zprávy
                await after.delete()

                # Získání objektu uživatele pro avatar
                user = self.bot.get_user(author_id)
                avatar_url = user.display_avatar.url if user else None

                # Získání nebo vytvoření webhooků
                webhook = await self.get_or_create_webhook(before.channel)

                if webhook:
                    # Pošleme jednu zprávu přes webhook s vysvětlením a číslem
                    await webhook.send(
                        content=f"**{author_name}** upravil zprávu s číslem **{count}**. Upravování zpráv není povoleno!\n\n>>> **{count}**",
                        username=author_name,
                        avatar_url=avatar_url
                    )
                else:
                    # Fallback na normální zprávu, pokud webhook není dostupný
                    bot_message = await before.channel.send(
                        f"**{author_name}** upravil zprávu s číslem **{count}**. "
                        f"Upravování zpráv není povoleno! Zde je původní číslo: **{count}**"
                    )
                    await bot_message.add_reaction("✅")

            except discord.Forbidden:
                print("Bot doesn't have permission to delete messages")
            except Exception as e:
                print(f"Error handling edited message: {e}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Sleduje mazání zpráv v kanálu počítání"""
        # Kontrola, zda je zpráva z kanálu počítání
        if message.channel.id != COUNTING_CHANNEL_ID:
            return

        # Ignorujeme zprávy od botů
        if message.author.bot:
            return

        # Kontrola, zda je zpráva v cache a zda je to poslední platné číslo
        if message.id in self.message_cache and self.message_cache[message.id]["count"] == self.data["current_count"]:
            cached_message = self.message_cache[message.id]
            count = cached_message["count"]
            author_name = cached_message["author_name"]
            author_id = cached_message["author_id"]

            try:
                # Získání objektu uživatele pro avatar
                user = self.bot.get_user(author_id)
                avatar_url = user.display_avatar.url if user else None

                # Získání nebo vytvoření webhooků
                webhook = await self.get_or_create_webhook(message.channel)

                if webhook:
                    # Pošleme jednu zprávu přes webhook s vysvětlením a číslem
                    await webhook.send(
                        content=f"**{author_name}** smazal zprávu s číslem **{count}**. Mazání zpráv není povoleno!\n\n>>> **{count}**",
                        username=author_name,
                        avatar_url=avatar_url
                    )
                else:
                    # Fallback na normální zprávu, pokud webhook není dostupný
                    bot_message = await message.channel.send(
                        f"**{author_name}** smazal zprávu s číslem **{count}**. "
                        f"Mazání zpráv není povoleno! Zde je původní číslo: **{count}**"
                    )
                    await bot_message.add_reaction("✅")

            except Exception as e:
                print(f"Error handling deleted message: {e}")

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

    @commands.command(name="countblock")
    @commands.has_permissions(administrator=True)
    async def block_user_command(self, ctx, user: discord.Member, days: int = 1):
        """Zablokuje uživatele od psaní do kanálu počítání (admin only)

        Parametry:
            user: Uživatel, který má být zablokován
            days: Počet dní blokace (výchozí: 1)
        """
        # Kontrola, zda je příkaz použit v kanálu pro počítání
        if ctx.channel.id != COUNTING_CHANNEL_ID:
            try:
                await ctx.message.delete()
                await ctx.author.send(f"Příkaz !countblock lze použít pouze v kanálu pro počítání <#{COUNTING_CHANNEL_ID}>")
            except Exception as e:
                print(f"Chyba při mazání zprávy nebo posílání DM: {str(e)}")
            return

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        # Kontrola, zda uživatel není admin
        if user.guild_permissions.administrator:
            await ctx.send(f"**{user.display_name}** je administrátor a nemůže být zablokován.", delete_after=5)
            return

        # Kontrola, zda je uživatel již blokován
        if self.is_user_blocked(user.id):
            await ctx.send(f"**{user.display_name}** je již blokován v kanálu pro počítání.", delete_after=5)
            return

        # Kontrola platnosti počtu dní
        if days < 1:
            await ctx.send(f"Počet dní blokace musí být alespoň 1.", delete_after=5)
            return

        # Blokování uživatele
        success = await self.block_user(user.id, user, None, days)

        if success:
            # Aktualizace statistik uživatele
            user_id = str(user.id)
            if user_id not in self.data["user_stats"]:
                self.data["user_stats"][user_id] = {
                    "username": user.display_name,
                    "correct_counts": 0,
                    "wrong_counts": 0,
                    "last_updated": None,
                    "consecutive_fails": 0,
                    "total_blocks": 0
                }

            self.data["user_stats"][user_id]["total_blocks"] += 1
            self.save_data()

            await ctx.send(f"**{user.display_name}** byl zablokován v kanálu pro počítání na {days} {'den' if days == 1 else 'dny' if days < 5 else 'dní'}.")

            # Informování uživatele
            try:
                await user.send(
                    f"Byl jsi zablokován v kanálu pro počítání na {days} {'den' if days == 1 else 'dny' if days < 5 else 'dní'} "
                    f"administrátorem {ctx.author.display_name}."
                )
            except:
                pass
        else:
            await ctx.send(f"Nepodařilo se zablokovat uživatele **{user.display_name}**.", delete_after=5)

    @commands.command(name="countblocked")
    @commands.has_permissions(administrator=True)
    async def list_blocked_users(self, ctx):
        """Zobrazí seznam blokovaných uživatelů (admin only)"""
        # Kontrola, zda je příkaz použit v kanálu pro počítání
        if ctx.channel.id != COUNTING_CHANNEL_ID:
            try:
                await ctx.message.delete()
                await ctx.author.send(f"Příkaz !countblocked lze použít pouze v kanálu pro počítání <#{COUNTING_CHANNEL_ID}>")
            except Exception as e:
                print(f"Chyba při mazání zprávy nebo posílání DM: {str(e)}")
            return

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        # Získání seznamu blokovaných uživatelů
        blocked_users = []
        for user_id, block_data in self.data["blocked_users"].items():
            end_time = datetime.datetime.fromisoformat(block_data["end_time"])
            now = datetime.datetime.now()

            if end_time > now:
                username = block_data["username"]
                blocked_at = datetime.datetime.fromisoformat(block_data["blocked_at"])
                duration = block_data["duration_days"]

                time_left = end_time - now
                days = time_left.days
                hours = time_left.seconds // 3600
                minutes = (time_left.seconds % 3600) // 60

                time_str = ""
                if days > 0:
                    time_str += f"{days} {'den' if days == 1 else 'dny' if days < 5 else 'dní'} "
                if hours > 0:
                    time_str += f"{hours} {'hodinu' if hours == 1 else 'hodiny' if hours < 5 else 'hodin'} "
                if minutes > 0 and days == 0:
                    time_str += f"{minutes} {'minutu' if minutes == 1 else 'minuty' if minutes < 5 else 'minut'}"

                blocked_users.append({
                    "user_id": user_id,
                    "username": username,
                    "blocked_at": blocked_at,
                    "duration": duration,
                    "end_time": end_time,
                    "time_left": time_str.strip()
                })

        if not blocked_users:
            await ctx.send("Aktuálně nejsou žádní blokovaní uživatelé.")
            return

        # Vytvoření embedu se seznamem blokovaných uživatelů
        embed = discord.Embed(
            title="⛔ Blokovaní uživatelé",
            description=f"Seznam uživatelů blokovaných v kanálu pro počítání <#{COUNTING_CHANNEL_ID}>",
            color=discord.Color.red()
        )

        for user_data in blocked_users:
            embed.add_field(
                name=f"{user_data['username']} (ID: {user_data['user_id']})",
                value=(
                    f"**Blokován:** {user_data['blocked_at'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"**Doba blokace:** {user_data['duration']} {'den' if user_data['duration'] == 1 else 'dny' if user_data['duration'] < 5 else 'dní'}\n"
                    f"**Zbývá:** {user_data['time_left']}\n"
                    f"**Odblokování:** {user_data['end_time'].strftime('%d.%m.%Y %H:%M')}"
                ),
                inline=False
            )

        embed.set_footer(text=f"Pro odblokování uživatele použijte příkaz !countunblock @uživatel")

        await ctx.send(embed=embed)

    @commands.command(name="countunblock")
    @commands.has_permissions(administrator=True)
    async def unblock_user_command(self, ctx, user: discord.Member):
        """Odblokuje uživatele od psaní do kanálu počítání (admin only)"""
        # Kontrola, zda je příkaz použit v kanálu pro počítání
        if ctx.channel.id != COUNTING_CHANNEL_ID:
            try:
                await ctx.message.delete()
                await ctx.author.send(f"Příkaz !countunblock lze použít pouze v kanálu pro počítání <#{COUNTING_CHANNEL_ID}>")
            except Exception as e:
                print(f"Chyba při mazání zprávy nebo posílání DM: {str(e)}")
            return

        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        user_id = str(user.id)

        # Kontrola, zda je uživatel blokován
        if not self.is_user_blocked(user_id):
            await ctx.send(f"**{user.display_name}** není blokován v kanálu pro počítání.", delete_after=5)
            return

        # Odblokování uživatele
        channel = self.bot.get_channel(COUNTING_CHANNEL_ID)
        success = await self.unblock_user(user_id, user, channel)

        if success:
            # Resetování počtu po sobě jdoucích chyb
            if user_id in self.data["user_stats"]:
                self.data["user_stats"][user_id]["consecutive_fails"] = 0
                self.save_data()

            await ctx.send(f"**{user.display_name}** byl odblokován v kanálu pro počítání.")

            # Informování uživatele
            try:
                await user.send(f"Byl jsi odblokován v kanálu pro počítání administrátorem {ctx.author.display_name}.")
            except:
                pass
        else:
            await ctx.send(f"Nepodařilo se odblokovat uživatele **{user.display_name}**.", delete_after=5)

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
            "Upravování nebo mazání zpráv není povoleno - bot obnoví smazané nebo upravené zprávy",
            f"Pokud pokazíte počítání {FIRST_BAN_THRESHOLD}x za sebou, budete zablokováni na {FIRST_BAN_DURATION} den",
            f"Pokud po odblokování pokazíte počítání znovu {SECOND_BAN_THRESHOLD}x, budete zablokováni na {SECOND_BAN_DURATION} dny",
            "Žádné podvádění nebo používání botů k počítání"
        ]

        for i, rule in enumerate(rules, 1):
            embed.add_field(name=f"Pravidlo {i}", value=rule, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="countstats")
    async def count_stats(self, ctx, user: discord.Member = None):
        """Show counting statistics for top 10 users or specific user"""
        if not self.data["user_stats"]:
            await ctx.send("Zatím nejsou k dispozici žádné statistiky počítání.")
            return

        # Pokud je zadán konkrétní uživatel, zobrazíme jeho statistiky
        if user:
            user_id = str(user.id)

            # Kontrola, zda máme statistiky pro tohoto uživatele
            if user_id not in self.data["user_stats"]:
                await ctx.send(f"**{user.display_name}** zatím nemá žádné statistiky počítání.")
                return

            stats = self.data["user_stats"][user_id]
            correct = stats["correct_counts"]
            wrong = stats["wrong_counts"]
            total = correct + wrong
            accuracy = (correct / total * 100) if total > 0 else 0
            consecutive_fails = stats.get("consecutive_fails", 0)
            total_blocks = stats.get("total_blocks", 0)

            # Vytvoření embedu pro konkrétního uživatele
            embed = discord.Embed(
                title=f"📊 Statistiky počítání - {user.display_name}",
                description=f"Podrobné statistiky uživatele v kanálu pro počítání",
                color=discord.Color.blue()
            )

            # Přidání avataru uživatele
            embed.set_thumbnail(url=user.display_avatar.url)

            # Základní statistiky
            embed.add_field(
                name="Základní statistiky",
                value=(
                    f"**Správné počty:** {correct}\n"
                    f"**Chybné počty:** {wrong}\n"
                    f"**Celkem pokusů:** {total}\n"
                    f"**Přesnost:** {accuracy:.1f}%"
                ),
                inline=False
            )

            # Statistiky blokací
            block_info = []
            if consecutive_fails > 0:
                block_info.append(f"**Po sobě jdoucí chyby:** {consecutive_fails}")
            if total_blocks > 0:
                block_info.append(f"**Počet blokací:** {total_blocks}")

            # Kontrola, zda je uživatel aktuálně blokován
            if user_id in self.data["blocked_users"]:
                block_data = self.data["blocked_users"][user_id]
                end_time = datetime.datetime.fromisoformat(block_data["end_time"])
                now = datetime.datetime.now()

                if end_time > now:
                    time_left = end_time - now
                    days = time_left.days
                    hours = time_left.seconds // 3600
                    minutes = (time_left.seconds % 3600) // 60

                    time_str = ""
                    if days > 0:
                        time_str += f"{days} {'den' if days == 1 else 'dny' if days < 5 else 'dní'} "
                    if hours > 0:
                        time_str += f"{hours} {'hodinu' if hours == 1 else 'hodiny' if hours < 5 else 'hodin'} "
                    if minutes > 0 and days == 0:
                        time_str += f"{minutes} {'minutu' if minutes == 1 else 'minuty' if minutes < 5 else 'minut'}"

                    block_info.append(f"**⛔ Aktuálně blokován do:** {end_time.strftime('%d.%m.%Y %H:%M')}")
                    block_info.append(f"**⏱️ Zbývá:** {time_str.strip()}")

            if block_info:
                embed.add_field(
                    name="Informace o blokacích",
                    value="\n".join(block_info),
                    inline=False
                )

            # Informace o pravidlech
            embed.add_field(
                name="Pravidla blokování",
                value=(
                    f"Po {FIRST_BAN_THRESHOLD} chybách za sebou - blokace na {FIRST_BAN_DURATION} den\n"
                    f"Po dalších {SECOND_BAN_THRESHOLD} chybách - blokace na {SECOND_BAN_DURATION} dny"
                ),
                inline=False
            )

            embed.set_footer(text=f"Celkový rekord serveru: {self.data['high_score']}")

            await ctx.send(embed=embed)
            return

        # Jinak zobrazíme top 10 uživatelů
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

        for i, (user_id_str, stats) in enumerate(top_users, 1):
            username = stats["username"]
            correct = stats["correct_counts"]
            wrong = stats["wrong_counts"]
            total = correct + wrong
            accuracy = (correct / total * 100) if total > 0 else 0
            consecutive_fails = stats.get("consecutive_fails", 0)
            total_blocks = stats.get("total_blocks", 0)

            value = f"**Správné počty:** {correct}\n"
            value += f"**Chybné počty:** {wrong}\n"
            value += f"**Přesnost:** {accuracy:.1f}%"

            # Přidání informací o blokacích
            if consecutive_fails > 0:
                value += f"\n**Po sobě jdoucí chyby:** {consecutive_fails}"
            if total_blocks > 0:
                value += f"\n**Počet blokací:** {total_blocks}"

            # Kontrola, zda je uživatel aktuálně blokován
            if user_id_str in self.data["blocked_users"]:
                block_data = self.data["blocked_users"][user_id_str]
                end_time = datetime.datetime.fromisoformat(block_data["end_time"])
                now = datetime.datetime.now()

                if end_time > now:
                    time_left = end_time - now
                    days = time_left.days
                    hours = time_left.seconds // 3600

                    time_str = ""
                    if days > 0:
                        time_str += f"{days}d "
                    if hours > 0 or days > 0:
                        time_str += f"{hours}h"

                    value += f"\n**⛔ Blokován ještě:** {time_str.strip()}"

            embed.add_field(
                name=f"{i}. {username}",
                value=value,
                inline=True
            )

            # Add empty field every 2 entries for better formatting
            if i % 2 == 0 and i < len(top_users):
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Přidání informací o aktuálně blokovaných uživatelích
        blocked_users = []
        for user_id, block_data in self.data["blocked_users"].items():
            end_time = datetime.datetime.fromisoformat(block_data["end_time"])
            now = datetime.datetime.now()

            if end_time > now:
                username = block_data["username"]
                time_left = end_time - now
                days = time_left.days
                hours = time_left.seconds // 3600

                time_str = ""
                if days > 0:
                    time_str += f"{days}d "
                if hours > 0 or days > 0:
                    time_str += f"{hours}h"

                blocked_users.append(f"**{username}** - ještě {time_str.strip()}")

        if blocked_users:
            embed.add_field(
                name="⛔ Aktuálně blokovaní uživatelé",
                value="\n".join(blocked_users),
                inline=False
            )

        embed.set_footer(text=f"Celkem počet selhání: {self.data['failed_counts']} | Blokace po {FIRST_BAN_THRESHOLD} chybách")

        await ctx.send(embed=embed)

    @commands.command(name="countformats")
    async def count_formats(self, ctx):
        """Show the supported number formats for counting"""
        # Smazání zprávy s příkazem
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Chyba při mazání zprávy: {str(e)}")

        embed = discord.Embed(
            title="🔢 Podporované formáty čísel",
            description="Při počítání můžete zadávat čísla v následujících formátech:",
            color=discord.Color.light_grey()
        )

        embed.add_field(
            name="Desítková (Decimal)",
            value="Standardní čísla.\n*Příklad:* `123`",
            inline=False
        )
        embed.add_field(
            name="Šestnáctková (Hexadecimal)",
            value="Čísla začínající prefixem `0x`.\n*Příklad:* `0xFF` (rovno 255)",
            inline=False
        )
        embed.add_field(
            name="Binární (Binary)",
            value="Čísla začínající prefixem `0b`.\n*Příklad:* `0b1011` (rovno 11)",
            inline=False
        )
        embed.add_field(
            name="Osmičková (Octal)",
            value="Čísla začínající prefixem `0o`.\n*Příklad:* `0o17` (rovno 15)",
            inline=False
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Counting(bot))
