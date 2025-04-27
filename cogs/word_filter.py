import discord
from discord.ext import commands
import os
import json
import re
from utils import config

# Načtení proměnných z konfigurace
AUDIT_LOG_CHANNEL_ID = config.get_int('AUDIT_LOG_CHANNEL_ID')

# Výchozí blacklist rasistických a nevhodných slov
DEFAULT_BLACKLISTED_WORDS = [
    # Rasistické výrazy
    "negr", "neger", "niger", "nigga", "nigger", "cikán", "cigoš", "cigoši", "cikáni", "žiďák", "židák",
    # Homofobní výrazy
    "buzna", "buzerant", "teplouš", "homouš", "fagot", "faggot",
    # Další nevhodné výrazy
    "retard", "mongol", "debil", "idiot", "kretén", "kreten"
]

# Globální proměnná pro blacklist, bude naplněna při inicializaci
BLACKLISTED_WORDS = []

class WordFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audit_channel = None
        self.filtered_messages_path = "db/filtered_words.json"
        self.blacklist_path = "db/blacklist_words.json"
        self.filtered_messages = self.load_filtered_messages()

        # Vytvoření složky db, pokud neexistuje
        os.makedirs("db", exist_ok=True)

        # Načtení blacklistu
        global BLACKLISTED_WORDS
        BLACKLISTED_WORDS = self.load_blacklist()

    def load_filtered_messages(self):
        """Načte data o filtrovaných zprávách z JSON souboru"""
        try:
            with open(self.filtered_messages_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"filtered_messages": []}

    def save_filtered_messages(self):
        """Uloží data o filtrovaných zprávách do JSON souboru"""
        with open(self.filtered_messages_path, 'w', encoding='utf-8') as file:
            json.dump(self.filtered_messages, file, ensure_ascii=False, indent=4)

    def load_blacklist(self):
        """Načte blacklist slov z JSON souboru"""
        try:
            with open(self.blacklist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get("blacklisted_words", [])
        except (FileNotFoundError, json.JSONDecodeError):
            # Pokud soubor neexistuje nebo je poškozený, použijeme výchozí blacklist
            # a vytvoříme nový soubor
            self.save_blacklist(DEFAULT_BLACKLISTED_WORDS)
            return DEFAULT_BLACKLISTED_WORDS

    def save_blacklist(self, words_list):
        """Uloží blacklist slov do JSON souboru"""
        data = {"blacklisted_words": words_list}
        with open(self.blacklist_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        """Inicializace po připravení bota"""
        if AUDIT_LOG_CHANNEL_ID:
            self.audit_channel = self.bot.get_channel(AUDIT_LOG_CHANNEL_ID)
            if self.audit_channel:
                print(f"Word filter nastaven s audit kanálem: #{self.audit_channel.name}")
            else:
                print(f"Varování: Audit log kanál s ID {AUDIT_LOG_CHANNEL_ID} nebyl nalezen pro word filter!")
        else:
            print("Audit log kanál není nastaven v .env souboru (AUDIT_LOG_CHANNEL_ID) pro word filter")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Kontroluje zprávy na nevhodná slova"""
        # Ignorujeme zprávy od botů a soukromé zprávy
        if message.author.bot or not message.guild:
            return

        # Ignorujeme zprávy od administrátorů
        if message.author.guild_permissions.administrator:
            return

        # Kontrola obsahu zprávy
        content = message.content.lower()

        # Kontrola na blacklistovaná slova
        found_words = []
        for word in BLACKLISTED_WORDS:
            # Použijeme regulární výraz pro hledání celých slov
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, content):
                found_words.append(word)

        if found_words:
            # Smazání zprávy
            try:
                await message.delete()

                # Uložení informací o smazané zprávě
                message_data = {
                    "user_id": str(message.author.id),
                    "username": message.author.name,
                    "channel_id": str(message.channel.id),
                    "channel_name": message.channel.name,
                    "content": message.content,
                    "found_words": found_words,
                    "timestamp": message.created_at.isoformat()
                }

                self.filtered_messages["filtered_messages"].append(message_data)
                self.save_filtered_messages()

                # Neposíláme žádné zprávy uživateli

                # Odeslání informace do audit logu
                if self.audit_channel:
                    audit_embed = discord.Embed(
                        title="🛑 Rasistický/nevhodný obsah detekován",
                        description=f"**Uživatel:** {message.author.mention} ({message.author.name})\n"
                                   f"**Kanál:** {message.channel.mention}\n"
                                   f"**Nalezená slova:** {', '.join(found_words)}",
                        color=discord.Color.dark_red(),
                        timestamp=message.created_at
                    )

                    # Přidáme obsah zprávy
                    if len(message.content) > 1024:
                        audit_embed.add_field(name="Obsah zprávy", value=f"{message.content[:1021]}...", inline=False)
                    else:
                        audit_embed.add_field(name="Obsah zprávy", value=message.content, inline=False)

                    audit_embed.set_footer(text=f"ID uživatele: {message.author.id}")

                    await self.audit_channel.send(embed=audit_embed)

            except discord.Forbidden:
                print(f"Bot nemá oprávnění smazat zprávu v kanálu {message.channel.name}")
            except discord.NotFound:
                print("Zpráva již byla smazána")
            except Exception as e:
                print(f"Chyba při mazání zprávy: {e}")



    @commands.command(name="blacklist_add")
    @commands.has_permissions(administrator=True)
    async def blacklist_add(self, ctx, *, word: str):
        """Přidá slovo do blacklistu (admin only, pouze v audit kanálu)"""
        # Kontrola, zda je příkaz použit v audit kanálu
        if ctx.channel.id != AUDIT_LOG_CHANNEL_ID:
            # Tiše ignorujeme, pokud není v audit kanálu
            try:
                await ctx.message.delete()
            except:
                pass
            return

        # Kontrola, zda je uživatel admin (pro jistotu, i když už to kontroluje dekorátor)
        if not ctx.author.guild_permissions.administrator:
            # Tiše ignorujeme, pokud není admin
            try:
                await ctx.message.delete()
            except:
                pass
            return

        # Zpracování příkazu
        word = word.lower().strip()

        # Smazání původní zprávy s příkazem
        try:
            await ctx.message.delete()
        except:
            pass

        if word in BLACKLISTED_WORDS:
            # Slovo už je v blacklistu, neděláme nic
            return

        # Přidání slova do blacklistu
        BLACKLISTED_WORDS.append(word)

        # Uložení aktualizovaného blacklistu do souboru
        self.save_blacklist(BLACKLISTED_WORDS)

        # Odeslání potvrzení pouze do audit kanálu
        embed = discord.Embed(
            title="✅ Slovo přidáno do blacklistu",
            description=f"Slovo `{word}` bylo přidáno do blacklistu.",
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(WordFilter(bot))
