import discord
from discord.ext import commands
import json
import os
from datetime import datetime

class Bookmarks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bookmarks_file = "data/bookmarks.json"
        self.bookmarks = self.load_bookmarks()

    def load_bookmarks(self):
        """Načte bookmarky ze souboru"""
        if not os.path.exists("data"):
            os.makedirs("data")
        
        if os.path.exists(self.bookmarks_file):
            with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_bookmarks(self):
        """Uloží bookmarky do souboru"""
        with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
            json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)

    @commands.command(name="bookmark", aliases=["bm"])
    async def bookmark(self, ctx, *, note: str = None):
        """Uloží zprávu jako bookmark
        
        Použití:
        !bookmark - Uloží zprávu, na kterou je odpovězeno
        !bookmark Poznámka - Uloží zprávu s vlastní poznámkou
        """
        # Kontrola, zda je příkaz použit jako odpověď na zprávu
        if not ctx.message.reference:
            await ctx.send("Tento příkaz musí být použit jako odpověď na zprávu, kterou chceš uložit.", ephemeral=True)
            return

        # Získání původní zprávy
        original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        
        # Vytvoření záznamu o bookmarku
        bookmark_data = {
            "content": original_message.content,
            "author": original_message.author.name,
            "author_id": str(original_message.author.id),
            "channel_name": original_message.channel.name,
            "channel_id": str(original_message.channel.id),
            "message_id": str(original_message.id),
            "timestamp": original_message.created_at.isoformat(),
            "jump_url": original_message.jump_url,
            "note": note,
            "saved_at": datetime.now().isoformat()
        }

        # Přidání attachmentů, pokud existují
        if original_message.attachments:
            bookmark_data["attachments"] = [att.url for att in original_message.attachments]

        # Uložení bookmarku
        user_id = str(ctx.author.id)
        if user_id not in self.bookmarks:
            self.bookmarks[user_id] = []
        
        self.bookmarks[user_id].append(bookmark_data)
        self.save_bookmarks()

        # Vytvoření embedu pro DM
        embed = discord.Embed(
            title="Nový bookmark uložen",
            description=original_message.content,
            color=discord.Color.blue(),
            timestamp=original_message.created_at
        )
        
        embed.add_field(
            name="Autor", 
            value=f"{original_message.author.name} ({original_message.author.id})",
            inline=True
        )
        embed.add_field(
            name="Kanál", 
            value=f"#{original_message.channel.name}",
            inline=True
        )
        if note:
            embed.add_field(name="Poznámka", value=note, inline=False)
        
        embed.add_field(name="Odkaz na zprávu", value=f"[Klikni zde]({original_message.jump_url})", inline=False)
        
        # Poslání potvrzení do DM
        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            await ctx.send("Bookmark byl uložen, ale nemohl jsem ti poslat potvrzení do DM. Zkontroluj, zda máš povolené DM zprávy.", ephemeral=True)

    @commands.command(name="bookmarks", aliases=["bms"])
    async def list_bookmarks(self, ctx, page: int = 1):
        """Zobrazí seznam uložených bookmarků
        
        Použití:
        !bookmarks - Zobrazí první stránku bookmarků
        !bookmarks 2 - Zobrazí druhou stránku bookmarků
        """
        user_id = str(ctx.author.id)
        if user_id not in self.bookmarks or not self.bookmarks[user_id]:
            await ctx.send("Nemáš uložené žádné bookmarky.", ephemeral=True)
            return

        # Stránkování
        items_per_page = 5
        bookmarks = self.bookmarks[user_id]
        pages = (len(bookmarks) + items_per_page - 1) // items_per_page
        
        if page < 1 or page > pages:
            await ctx.send(f"Stránka {page} neexistuje. Dostupné stránky: 1-{pages}", ephemeral=True)
            return

        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(bookmarks))

        embed = discord.Embed(
            title="Tvoje bookmarky",
            description=f"Stránka {page}/{pages}",
            color=discord.Color.blue()
        )

        for idx, bm in enumerate(bookmarks[start_idx:end_idx], start=start_idx + 1):
            content = bm["content"][:100] + "..." if len(bm["content"]) > 100 else bm["content"]
            field_text = f"**Kanál:** #{bm['channel_name']}\n"
            field_text += f"**Autor:** {bm['author']}\n"
            field_text += f"**Obsah:** {content}\n"
            if bm.get("note"):
                field_text += f"**Poznámka:** {bm['note']}\n"
            field_text += f"[Odkaz na zprávu]({bm['jump_url']})"
            
            embed.add_field(
                name=f"Bookmark {idx}",
                value=field_text,
                inline=False
            )

        await ctx.author.send(embed=embed)
        if ctx.guild:
            await ctx.message.add_reaction("✅")

    @commands.command(name="bookmark_delete", aliases=["bmd"])
    async def delete_bookmark(self, ctx, index: int):
        """Smaže bookmark podle indexu
        
        Použití:
        !bookmark_delete 1 - Smaže první bookmark
        """
        user_id = str(ctx.author.id)
        if user_id not in self.bookmarks or not self.bookmarks[user_id]:
            await ctx.send("Nemáš uložené žádné bookmarky.", ephemeral=True)
            return

        if index < 1 or index > len(self.bookmarks[user_id]):
            await ctx.send(f"Neplatný index. Zadej číslo mezi 1 a {len(self.bookmarks[user_id])}.", ephemeral=True)
            return

        # Smazání bookmarku
        deleted_bookmark = self.bookmarks[user_id].pop(index - 1)
        self.save_bookmarks()

        embed = discord.Embed(
            title="Bookmark smazán",
            description=f"Bookmark byl úspěšně smazán:\n{deleted_bookmark['content'][:100]}...",
            color=discord.Color.red()
        )

        await ctx.author.send(embed=embed)
        if ctx.guild:
            await ctx.message.add_reaction("✅")

async def setup(bot):
    await bot.add_cog(Bookmarks(bot))
