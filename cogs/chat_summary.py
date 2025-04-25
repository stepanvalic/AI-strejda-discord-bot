import os
import json
import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from datetime import datetime, time, timedelta
from utils import chat_db, config
from discord.ext.commands import CommandOnCooldown, BucketType

# Load configuration
CHAT_ID = config.get_int('SUMMARY_CHAT_ID', 0)
SUMMARY_CHANNEL_ID = config.get_int('SUMMARY_CHANNEL_ID', 0)
OPENROUTER_API_KEY = config.get('OPENROUTER_API_KEY', '')
OPENROUTER_MODEL = config.get('OPENROUTER_MODEL', '')
SUMMARY_COOLDOWN_HOURS = config.get_int('SUMMARY_COOLDOWN_HOURS', 6)

class ChatSummary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.summary_channel = None

        # Ensure directories exist
        os.makedirs("db", exist_ok=True)
        os.makedirs("db/sumar", exist_ok=True)
        print(f"[Summary] Ensuring directories exist: db and db/sumar")

        self.daily_summary.start()

    def cog_unload(self):
        self.daily_summary.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and store them in the database"""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return

        # Only store messages from the specified chat
        if CHAT_ID != 0 and message.channel.id != CHAT_ID:
            # Pokud je CHAT_ID nastaveno, ukládáme pouze zprávy z tohoto kanálu
            print(f"[Summary] Ignoring message from channel {message.channel.name} (ID: {message.channel.id}) - not the target channel (ID: {CHAT_ID})")
            return

        # Store message data
        message_data = {
            "user_id": str(message.author.id),
            "username": message.author.name,
            "display_name": message.author.display_name,
            "channel_id": str(message.channel.id),
            "channel_name": message.channel.name,
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "message_id": str(message.id),
            "has_attachments": len(message.attachments) > 0,
            "has_embeds": len(message.embeds) > 0,
            "jump_url": message.jump_url
        }

        # Save to database
        try:
            chat_db.save_message(message_data)
            print(f"[Summary] Saved message from {message.author.display_name} in channel {message.channel.name} (ID: {message.channel.id})")
        except Exception as e:
            print(f"[Summary] Error saving message to database: {e}")

    @tasks.loop(time=time(hour=3, minute=0))  # Run at 3 AM every day
    async def daily_summary(self):
        """Generate and send daily summary at 3 AM"""
        print("[Summary] Starting daily summary generation...")

        # Get yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Check if we already have a summary for yesterday
        existing_summary = chat_db.get_summary_by_date(yesterday)
        if existing_summary:
            print(f"[Summary] Summary for {yesterday} already exists, skipping")
            return

        # Get messages from yesterday
        messages = chat_db.get_messages_by_date(yesterday)

        if not messages:
            print(f"[Summary] No messages found for {yesterday}, skipping")
            return

        print(f"[Summary] Found {len(messages)} messages for {yesterday}")

        # Generate summary
        summary = await self.generate_summary(messages, yesterday)

        if not summary:
            print("[Summary] Failed to generate summary")
            return

        # Extract message IDs from the summary for topic beginnings
        import re
        topic_links = re.findall(r'<https://discord\.com/channels/\d+/\d+/(\d+)>', summary)

        # Save summary to database with message IDs for topics
        summary_data = {
            "date": yesterday,
            "message_count": len(messages),
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "topic_message_ids": topic_links
        }

        chat_db.save_summary(summary_data)

        # Send summary to the default channel
        await self.send_summary(summary_data)

        # Clean up old messages (keep last 30 days)
        remaining_messages = chat_db.clean_old_messages(30)
        print(f"[Summary] Cleaned up old messages, {remaining_messages} messages remaining")

    @daily_summary.before_loop
    async def before_daily_summary(self):
        """Wait for the bot to be ready before starting the task"""
        await self.bot.wait_until_ready()

    async def generate_summary(self, messages, date):
        """Generate a summary of the messages using OpenRouter API"""
        if not OPENROUTER_API_KEY:
            print("[Summary] OpenRouter API key is missing")
            return None

        if not OPENROUTER_MODEL:
            print("[Summary] OpenRouter model is not specified")
            return None

        print(f"[Summary] Generating summary for {date} with {len(messages)} messages using model {OPENROUTER_MODEL}")

        # Prepare messages for the API
        message_texts = []
        message_map = {}  # Map to store message IDs for reference

        for msg in messages:
            username = msg.get("display_name") or msg.get("username", "Unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")[:19]  # Truncate to remove microseconds
            message_id = msg.get("message_id", "")
            channel_id = msg.get("channel_id", "")

            # Skip empty messages
            if not content.strip():
                continue

            # Format message with ID for reference
            formatted_message = f"[{timestamp}] {username}: {content}"
            message_texts.append(formatted_message)

            # Store message ID with its index for later reference
            message_map[len(message_texts) - 1] = {
                "message_id": message_id,
                "channel_id": channel_id,
                "timestamp": timestamp,
                "username": username
            }

        # Join messages with newlines
        all_messages = "\n".join(message_texts)

        # Prepare prompt for the API
        system_prompt = (
            "Jsi asistent, který vytváří denní shrnutí diskuzí z Discord chatu. "
            "Tvým úkolem je analyzovat zprávy a vytvořit strukturované shrnutí hlavních témat, "
            "která se v chatu probírala. Shrnutí by mělo být v češtině a mělo by být rozděleno "
            "podle témat. Pro každé téma identifikuj první zprávu, která toto téma začíná, a označ ji jako 'TOPIC_START:index', "
            "kde index je pořadové číslo zprávy v seznamu (začíná od 0). "
            "Zahrň odkazy na zprávy, které jsou v textu (začínají http:// nebo https://). "
            "Formát výstupu by měl být následující:\n\n"
            "## Téma 1 [TOPIC_START:5]\n"
            "Shrnutí tématu 1...\n\n"
            "## Téma 2 [TOPIC_START:12]\n"
            "Shrnutí tématu 2...\n\n"
            "Kde čísla 5 a 12 jsou indexy zpráv, které začínají dané téma. "
            "Tyto indexy budou později nahrazeny odkazy na konkrétní zprávy, což umožní uživatelům "
            "přejít přímo na začátek daného tématu v historii chatu. Je důležité, aby každé téma "
            "mělo označení [TOPIC_START:index] hned za jeho názvem."
        )

        user_prompt = (
            f"Zde jsou zprávy z Discord chatu ze dne {date}. Vytvoř strukturované shrnutí "
            f"hlavních témat, která se probírala. Rozděl shrnutí podle témat a zahrň důležité "
            f"body diskuze. Pro každé téma identifikuj první zprávu, která toto téma začíná, a označ ji jako 'TOPIC_START:index'. "
            f"Formát by měl být: '## Název tématu [TOPIC_START:index]'. "
            f"Pokud se v textu vyskytují odkazy, zahrň je do shrnutí. "
            f"Nezapomeň, že každé téma musí mít označení [TOPIC_START:index], aby uživatelé mohli kliknout na odkaz a přejít na začátek tématu.\n\n"
            f"{all_messages}"
        )

        # Call OpenRouter API
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }

                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[Summary] OpenRouter API error: {response.status} - {error_text}")
                        return None

                    data = await response.json()

                    if not data.get("choices") or not data["choices"][0].get("message"):
                        print(f"[Summary] Invalid response from OpenRouter API: {data}")
                        return None

                    summary = data["choices"][0]["message"]["content"]

                    # Process the summary to replace TOPIC_START markers with actual message links
                    import re
                    topic_start_pattern = r'\[TOPIC_START:(\d+)\]'

                    def replace_topic_start(match):
                        index = int(match.group(1))
                        if index in message_map:
                            msg_info = message_map[index]
                            message_id = msg_info["message_id"]
                            channel_id = msg_info["channel_id"]
                            # Format for clickable message link in Discord
                            return f"<https://discord.com/channels/{config.get_int('GUILD_ID')}/{channel_id}/{message_id}>"
                        return ""

                    processed_summary = re.sub(topic_start_pattern, replace_topic_start, summary)
                    return processed_summary

        except Exception as e:
            print(f"[Summary] Error calling OpenRouter API: {e}")
            return None

    async def send_summary(self, summary_data, channel_id=None):
        """Send the summary to the designated channel or a specific channel"""
        target_channel_id = channel_id or SUMMARY_CHANNEL_ID

        if not target_channel_id:
            print("[Summary] Summary channel ID is not set")
            return

        # Get the channel
        target_channel = self.bot.get_channel(target_channel_id)

        if not target_channel:
            print(f"[Summary] Channel with ID {target_channel_id} not found")
            return

        # Update the summary channel if we're using the default
        if not channel_id and not self.summary_channel:
            self.summary_channel = target_channel

        # Create embed
        date = summary_data.get("date", "Unknown date")
        message_count = summary_data.get("message_count", 0)
        summary = summary_data.get("summary", "No summary available")

        # Split summary into chunks if it's too long
        max_embed_description_length = 4096
        summary_chunks = []

        if len(summary) <= max_embed_description_length:
            summary_chunks = [summary]
        else:
            # Split by paragraphs first
            paragraphs = summary.split("\n\n")
            current_chunk = ""

            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) + 2 <= max_embed_description_length:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # If adding this paragraph would exceed the limit, save the current chunk and start a new one
                    if current_chunk:
                        summary_chunks.append(current_chunk)

                    # If the paragraph itself is too long, split it further
                    if len(paragraph) > max_embed_description_length:
                        # Split by sentences or just characters if needed
                        remaining = paragraph
                        while remaining:
                            chunk_size = min(max_embed_description_length, len(remaining))
                            summary_chunks.append(remaining[:chunk_size])
                            remaining = remaining[chunk_size:]
                    else:
                        current_chunk = paragraph

            # Add the last chunk if there's anything left
            if current_chunk:
                summary_chunks.append(current_chunk)

        # Send the first embed with the header
        first_embed = discord.Embed(
            title=f"📊 Shrnutí chatu za {date}",
            description=summary_chunks[0],
            color=discord.Color.blue()
        )

        first_embed.set_footer(text=f"Celkem zpráv: {message_count}")
        first_embed.timestamp = datetime.now()

        await target_channel.send(embed=first_embed)

        # Send additional embeds if needed
        for i, chunk in enumerate(summary_chunks[1:], 1):
            embed = discord.Embed(
                description=chunk,
                color=discord.Color.blue()
            )

            await target_channel.send(embed=embed)

    @commands.command(name="sumarizace-stepan")
    @commands.has_permissions(administrator=True)
    async def manual_summary(self, ctx, channel: discord.TextChannel = None):
        """Manually trigger a summary generation (admin only)

        Parameters:
        -----------
        channel: Volitelný kanál, kam poslat shrnutí
        """
        await ctx.send("Generuji shrnutí chatu...", ephemeral=True)

        # Get yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Get messages from yesterday
        try:
            messages = chat_db.get_messages_by_date(yesterday)
            print(f"[Summary] Manual summary: Found {len(messages)} messages for {yesterday}")
        except Exception as e:
            print(f"[Summary] Error getting messages by date: {e}")
            await ctx.send(f"Chyba při získávání zpráv: {e}", ephemeral=True)
            return

        if not messages:
            print(f"[Summary] Manual summary: No messages found for {yesterday}")
            await ctx.send(f"Žádné zprávy pro {yesterday} nebyly nalezeny.", ephemeral=True)
            return

        # Generate summary
        summary = await self.generate_summary(messages, yesterday)

        if not summary:
            await ctx.send("Nepodařilo se vygenerovat shrnutí.", ephemeral=True)
            return

        # Extract message IDs from the summary for topic beginnings
        import re
        topic_links = re.findall(r'<https://discord\.com/channels/\d+/\d+/(\d+)>', summary)

        # Save summary to database with message IDs for topics
        summary_data = {
            "date": yesterday,
            "message_count": len(messages),
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "topic_message_ids": topic_links
        }

        chat_db.save_summary(summary_data)

        # Get target channel ID
        target_channel_id = channel.id if channel else None

        # Send summary to channel
        await self.send_summary(summary_data, target_channel_id)

        # Prepare confirmation message
        if channel:
            await ctx.send(f"Shrnutí pro {yesterday} bylo vygenerováno a odesláno do kanálu {channel.mention}.", ephemeral=True)
        else:
            await ctx.send(f"Shrnutí pro {yesterday} bylo vygenerováno a odesláno do výchozího kanálu.", ephemeral=True)

    @commands.command(name="sumarizace")
    @commands.cooldown(1, SUMMARY_COOLDOWN_HOURS*60*60, BucketType.user)  # 1 use per X hours per user
    async def user_summary(self, ctx, count: int = 100):
        """Vygeneruje shrnutí posledních N zpráv a pošle ho do soukromé zprávy

        Parameters:
        -----------
        count: Počet zpráv k sumarizaci (výchozí: 100, maximum: 500)
        """
        # Check if count is within reasonable limits
        if count > 500:
            await ctx.send("Maximální počet zpráv pro sumarizaci je 500.", ephemeral=True)
            ctx.command.reset_cooldown(ctx)
            return

        if count < 10:
            await ctx.send("Minimální počet zpráv pro sumarizaci je 10.", ephemeral=True)
            ctx.command.reset_cooldown(ctx)
            return

        # Admin bypass for cooldown
        if ctx.author.guild_permissions.administrator:
            ctx.command.reset_cooldown(ctx)

        await ctx.send(f"Generuji shrnutí posledních {count} zpráv. Výsledek ti pošlu do soukromé zprávy.", ephemeral=True)

        try:
            # Get the latest messages
            messages = chat_db.get_latest_messages(count)
            print(f"[Summary] User summary: Found {len(messages)} messages for user {ctx.author.display_name}")

            if not messages:
                await ctx.send("Nenalezeny žádné zprávy k sumarizaci.", ephemeral=True)
                return

            # Generate summary
            current_date = datetime.now().strftime("%Y-%m-%d")
            summary = await self.generate_summary(messages, current_date)

            if not summary:
                await ctx.send("Nepodařilo se vygenerovat shrnutí.", ephemeral=True)
                return

            # Extract message IDs from the summary for topic beginnings
            import re
            topic_links = re.findall(r'<https://discord\.com/channels/\d+/\d+/(\d+)>', summary)

            # Create summary data
            summary_data = {
                "date": current_date,
                "message_count": len(messages),
                "summary": summary,
                "timestamp": datetime.now().isoformat(),
                "topic_message_ids": topic_links,
                "requested_by": str(ctx.author.id)
            }

            # Send summary to user via DM
            await self.send_summary_dm(ctx.author, summary_data)

            # Confirm to the user
            await ctx.send("Shrnutí bylo vygenerováno a posláno do tvých soukromých zpráv.", ephemeral=True)

        except Exception as e:
            print(f"[Summary] Error generating user summary: {e}")
            await ctx.send(f"Chyba při generování shrnutí: {e}", ephemeral=True)
            # Don't reset cooldown on error to prevent abuse

    async def send_summary_dm(self, user, summary_data):
        """Send the summary to a user via DM"""
        # Create embed
        message_count = summary_data.get("message_count", 0)
        summary = summary_data.get("summary", "No summary available")

        # Split summary into chunks if it's too long
        max_embed_description_length = 4096
        summary_chunks = []

        if len(summary) <= max_embed_description_length:
            summary_chunks = [summary]
        else:
            # Split by paragraphs first
            paragraphs = summary.split("\n\n")
            current_chunk = ""

            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) + 2 <= max_embed_description_length:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # If adding this paragraph would exceed the limit, save the current chunk and start a new one
                    if current_chunk:
                        summary_chunks.append(current_chunk)

                    # If the paragraph itself is too long, split it further
                    if len(paragraph) > max_embed_description_length:
                        # Split by sentences or just characters if needed
                        remaining = paragraph
                        while remaining:
                            chunk_size = min(max_embed_description_length, len(remaining))
                            summary_chunks.append(remaining[:chunk_size])
                            remaining = remaining[chunk_size:]
                    else:
                        current_chunk = paragraph

            # Add the last chunk if there's anything left
            if current_chunk:
                summary_chunks.append(current_chunk)

        # Send the first embed with the header
        first_embed = discord.Embed(
            title=f"📊 Shrnutí chatu",
            description=summary_chunks[0],
            color=discord.Color.blue()
        )

        first_embed.set_footer(text=f"Celkem zpráv: {message_count}")
        first_embed.timestamp = datetime.now()

        try:
            dm_channel = await user.create_dm()
            await dm_channel.send(embed=first_embed)

            # Send additional embeds if needed
            for i, chunk in enumerate(summary_chunks[1:], 1):
                embed = discord.Embed(
                    description=chunk,
                    color=discord.Color.blue()
                )

                await dm_channel.send(embed=embed)
        except discord.Forbidden:
            # User has DMs disabled
            print(f"[Summary] Could not send DM to {user.display_name} - DMs disabled")
        except Exception as e:
            print(f"[Summary] Error sending summary DM: {e}")

    @user_summary.error
    async def user_summary_error(self, ctx, error):
        """Handle errors for the user_summary command"""
        if isinstance(error, CommandOnCooldown):
            minutes, seconds = divmod(int(error.retry_after), 60)
            hours, minutes = divmod(minutes, 60)

            if hours > 0:
                await ctx.send(
                    f"Tento příkaz můžeš použít pouze jednou za {SUMMARY_COOLDOWN_HOURS} hodin. "
                    f"Zkus to znovu za {hours} hodin a {minutes} minut.",
                    ephemeral=True
                )
            elif minutes > 0:
                await ctx.send(
                    f"Tento příkaz můžeš použít pouze jednou za {SUMMARY_COOLDOWN_HOURS} hodin. "
                    f"Zkus to znovu za {minutes} minut a {seconds} sekund.",
                    ephemeral=True
                )
            else:
                await ctx.send(
                    f"Tento příkaz můžeš použít pouze jednou za {SUMMARY_COOLDOWN_HOURS} hodin. "
                    f"Zkus to znovu za {seconds} sekund.",
                    ephemeral=True
                )
        else:
            await ctx.send(f"Nastala chyba: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChatSummary(bot))
