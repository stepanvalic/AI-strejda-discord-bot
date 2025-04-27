import os
import json
import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import traceback
from datetime import datetime, time, timedelta
from utils import chat_db, config, token_tracker
from discord.ext.commands import CommandOnCooldown, BucketType
from openai import OpenAI

# Load configuration
CHAT_ID = config.get_int('SUMMARY_CHAT_ID')
SUMMARY_CHANNEL_ID = config.get_int('SUMMARY_CHANNEL_ID')
SUMMARY_API_PROVIDER = config.get('SUMMARY_API_PROVIDER')
DEEPSEEK_API_KEY = config.get('DEEPSEEK_API_KEY')
DEEPSEEK_MODEL = config.get('DEEPSEEK_MODEL')
SUMMARY_COOLDOWN_HOURS = config.get_int('SUMMARY_COOLDOWN_HOURS')

debug_print = print  # Remove debug_print function

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
        print(f"[Summary] Target date for summary: {yesterday} (yesterday)")

        # Check if we already have a summary for yesterday
        existing_summary = chat_db.get_summary_by_date(yesterday)
        if existing_summary:
            print(f"[Summary] Found existing summary for {yesterday}")
            print(f"[Summary] Existing summary info: message_count={existing_summary.get('message_count')}, manual={existing_summary.get('manual')}, auto_generated={existing_summary.get('auto_generated')}")

        # Get messages from yesterday
        messages = chat_db.get_messages_by_date(yesterday)
        print(f"[Summary] Retrieved {len(messages) if messages else 0} messages for {yesterday}")

        if not messages:
            print(f"[Summary] No messages found for {yesterday}, skipping")
            return

        print(f"[Summary] Found {len(messages)} messages for {yesterday}")

        # Log a sample of messages in debug mode
        sample_size = min(5, len(messages))
        print(f"[Summary] Sample of {sample_size} messages:")
        for i, msg in enumerate(messages[:sample_size]):
            username = msg.get("display_name") or msg.get("username", "Unknown")
            content = msg.get("content", "")
            print(f"[Summary]   Message {i+1}: {username}: {content[:100]}...")

        # If a summary already exists, check if it was manually created
        if existing_summary:
            # Check if it was manually created (has a requested_by field or was created during the day)
            is_manual = "requested_by" in existing_summary or (
                "timestamp" in existing_summary and
                existing_summary["timestamp"].startswith(yesterday)
            )

            if is_manual:
                print(f"[Summary] Manual summary for {yesterday} found, regenerating it")
            else:
                print(f"[Summary] Automatic summary for {yesterday} already exists, skipping")
                return

        # Generate summary
        print(f"[Summary] Generating summary for {yesterday} with {len(messages)} messages")
        summary = await self.generate_summary(messages, yesterday)

        if not summary:
            print("[Summary] Failed to generate summary")
            return

        print(f"[Summary] Summary generated successfully, length: {len(summary)} characters")
        print(f"[Summary] Summary preview (first 500 chars): {summary[:500]}...")

        # Extract message IDs from the summary for topic beginnings
        import re
        topic_links = re.findall(r'\[téma\]\(https://discord\.com/channels/\d+/\d+/(\d+)\)', summary)
        print(f"[Summary] Extracted {len(topic_links)} topic links from summary")

        if topic_links:
            print("[Summary] Topic links found:")
            for i, link in enumerate(topic_links):
                print(f"[Summary]   Topic {i+1}: Message ID {link}")

        # Save summary to database with message IDs for topics
        summary_data = {
            "date": yesterday,
            "message_count": len(messages),
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "topic_message_ids": topic_links,
            "auto_generated": True  # Mark as automatically generated
        }

        print(f"[Summary] Saving summary to database for date {yesterday}")
        chat_db.save_summary(summary_data)
        print("[Summary] Summary saved to database successfully")

        # Send summary to the default channel
        print("[Summary] Sending summary to the default channel")
        await self.send_summary(summary_data)
        print("[Summary] Summary sent successfully")

        # Clean up old messages (keep last 30 days)
        print("[Summary] Cleaning up old messages (keeping last 30 days)")
        remaining_messages = chat_db.clean_old_messages(30)
        print(f"[Summary] Cleaned up old messages, {remaining_messages} messages remaining")

    @daily_summary.before_loop
    async def before_daily_summary(self):
        """Wait for the bot to be ready before starting the task"""
        await self.bot.wait_until_ready()

    async def generate_summary(self, messages, date):
        """Generate a summary of the messages using either OpenRouter or DeepSeek API"""
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
            "📊 Shrnutí chatu za YYYY-MM-DD\n"
            "Shrnutí diskuzí z Discord chatu (DD. M. YYYY)\n"
            "---\n\n"
            "#### 1. Název tématu [TOPIC_START:5]\n"
            "Hlavní téma: Stručný popis hlavního tématu v jedné větě.\n"
            "Detaily: Podrobnější shrnutí diskuze, klíčové body, závěry.\n"
            "Odkazy: Seznam odkazů zmíněných v diskuzi (pokud existují).\n"
            "Vývoj: Jak se téma vyvíjelo, k jakému závěru diskuze dospěla.\n"
            "Citace: Zajímavé nebo důležité citace z diskuze (pokud existují).\n\n"
            "---\n\n"
            "#### 2. Název tématu [TOPIC_START:12]\n"
            "Hlavní téma: Stručný popis hlavního tématu v jedné větě.\n"
            "Detaily: Podrobnější shrnutí diskuze, klíčové body, závěry.\n"
            "Odkazy: Seznam odkazů zmíněných v diskuzi (pokud existují).\n"
            "Vývoj: Jak se téma vyvíjelo, k jakému závěru diskuze dospěla.\n"
            "Citace: Zajímavé nebo důležité citace z diskuze (pokud existují).\n\n"
            "---\n\n"
            "Kde čísla 5 a 12 jsou indexy zpráv, které začínají dané téma. "
            "Tyto indexy budou později nahrazeny odkazy na konkrétní zprávy ve formátu [téma](url), což umožní uživatelům "
            "přejít přímo na začátek daného tématu v historii chatu. Je důležité, aby každé téma "
            "mělo označení [TOPIC_START:index] hned za jeho názvem. "
            "Formátuj datum v hlavičce správně - DD. M. YYYY znamená den, měsíc a rok s tečkami (např. 18. 4. 2025)."
        )

        user_prompt = (
            f"Zde jsou zprávy z Discord chatu ze dne {date}. Vytvoř strukturované shrnutí "
            f"hlavních témat, která se probírala. Rozděl shrnutí podle témat a zahrň důležité "
            f"body diskuze. Pro každé téma identifikuj první zprávu, která toto téma začíná, a označ ji jako 'TOPIC_START:index'. "
            f"Formát by měl být: '#### N. Název tématu [TOPIC_START:index]', kde N je pořadové číslo tématu. "
            f"Každé téma by mělo obsahovat sekce: Hlavní téma (stručný popis), Detaily, Odkazy (pokud existují), "
            f"Vývoj a případně Citace. Mezi tématy vždy přidej oddělovač '---'. "
            f"Pokud se v textu vyskytují odkazy, zahrň je do shrnutí. "
            f"Nezapomeň, že každé téma musí mít označení [TOPIC_START:index], aby uživatelé mohli kliknout na odkaz a přejít na začátek tématu. "
            f"Tyto indexy budou později nahrazeny odkazy ve formátu [téma](url). "
            f"Na konci shrnutí přidej sekci 'Celkové shrnutí:' s krátkým souhrnem celého dne. "
            f"Pokud se v chatu vyskytl nějaký vtipný moment, přidej před celkové shrnutí sekci 'Nejvtipnější moment:'. "
            f"Formát hlavičky by měl být: '📊 Shrnutí chatu za {date}\\nShrnutí diskuzí z Discord chatu (DD. M. YYYY)\\n---'\n\n"
            f"{all_messages}"
        )

        print(f"[Summary] Prepared {len(message_texts)} messages for summarization")
        print(f"[Summary] System prompt length: {len(system_prompt)} chars")
        print(f"[Summary] User prompt length: {len(user_prompt)} chars")

        # Choose API provider based on configuration
        if not SUMMARY_API_PROVIDER:
            print("[Summary] API provider not specified in configuration")
            return None

        print(f"[Summary] API provider from config: {SUMMARY_API_PROVIDER}")

        if SUMMARY_API_PROVIDER.lower() != 'deepseek':
            print(f"[Summary] Unknown API provider: {SUMMARY_API_PROVIDER}")
            print(f"[Summary] Supported providers are 'deepseek'")
            return None

        # Use DeepSeek API
        if not DEEPSEEK_API_KEY:
            print("[Summary] DeepSeek API key is missing in environment variables")
            print("[Summary] Please add DEEPSEEK_API_KEY to your .env file")
            return None

        if not DEEPSEEK_MODEL:
            print("[Summary] DeepSeek model is not specified in configuration")
            return None

        print(f"[Summary] Generating summary for {date} with {len(messages)} messages using DeepSeek model {DEEPSEEK_MODEL}")
        print(f"[Summary] Using DeepSeek API with model {DEEPSEEK_MODEL}")

        try:
            # Initialize OpenAI client for DeepSeek API
            print(f"[Summary] Initializing OpenAI client with DeepSeek API base URL")
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v3"  # Changed from "https://api.deepseek.com/v1"
            )

            # Prepare messages for API
            print(f"[Summary] Preparing messages for DeepSeek API")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            print(f"[Summary] Request prepared with system prompt ({len(system_prompt)} chars) and user prompt ({len(user_prompt)} chars)")

            # Send request to API
            print(f"[Summary] Sending request to DeepSeek API using OpenAI SDK")
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=DEEPSEEK_MODEL,  # Use the configured model name
                messages=messages,
                stream=False
            )

            # Process response
            print(f"[Summary] DeepSeek API response received successfully")

            # Convert response to dictionary for token tracker
            print(f"[Summary] Converting response to dictionary for token tracking")
            response_dict = response.model_dump()
            print(f"[Summary] Response received with {response.usage.prompt_tokens} prompt tokens and {response.usage.completion_tokens} completion tokens")

            # Track token usage
            print(f"[Summary] Tracking token usage from DeepSeek API response")
            token_tracker.extract_tokens_from_deepseek_response(response_dict, "summary")

            # Extract content from response
            print(f"[Summary] Extracting content from DeepSeek API response")
            summary = response.choices[0].message.content
            print(f"[Summary] Successfully generated summary with DeepSeek API (length: {len(summary)} chars)")
            print(f"[Summary] Summary preview (first 100 chars): {summary[:100]}...")
        except Exception as e:
            print(f"[Summary] Error calling DeepSeek API: {e}")
            print(f"[Summary] Exception type: {type(e).__name__}")
            print(f"[Summary] Exception traceback: {traceback.format_exc()}")
            return None

        # Process the summary to replace TOPIC_START markers with actual message links
        import re
        topic_start_pattern = r'\[TOPIC_START:(\d+)\]'

        def replace_topic_start(match):
            index = int(match.group(1))
            if index in message_map:
                msg_info = message_map[index]
                message_id = msg_info["message_id"]
                channel_id = msg_info["channel_id"]
                # Format for clickable message link in Discord using [tema](url) format
                url = f"https://discord.com/channels/{config.get_int('GUILD_ID')}/{channel_id}/{message_id}"
                return f"[téma]({url})"
            return ""

        processed_summary = re.sub(topic_start_pattern, replace_topic_start, summary)
        return processed_summary

    async def send_summary(self, summary_data, channel_id=None):
        """Send the summary to the designated channel or a specific channel"""
        debug_print(f"Sending summary to channel, channel_id={channel_id or 'default'}")

        target_channel_id = channel_id or SUMMARY_CHANNEL_ID
        debug_print(f"Target channel ID: {target_channel_id}")

        if not target_channel_id:
            print("[Summary] Summary channel ID is not set")
            debug_print("Summary channel ID is not set, cannot send summary")
            return

        # Get the channel
        target_channel = self.bot.get_channel(target_channel_id)

        if not target_channel:
            print(f"[Summary] Channel with ID {target_channel_id} not found")
            debug_print(f"Channel with ID {target_channel_id} not found")
            return

        debug_print(f"Found target channel: {target_channel.name} (ID: {target_channel.id})")

        # Update the summary channel if we're using the default
        if not channel_id and not self.summary_channel:
            self.summary_channel = target_channel
            debug_print("Updated default summary channel reference")

        # Create embed
        date = summary_data.get("date", "Unknown date")
        message_count = summary_data.get("message_count", 0)
        summary = summary_data.get("summary", "No summary available")
        debug_print(f"Preparing summary for date {date}, message count: {message_count}, summary length: {len(summary)}")

        # Split summary into chunks if it's too long
        max_embed_description_length = 4096
        summary_chunks = []

        if len(summary) <= max_embed_description_length:
            summary_chunks = [summary]
            debug_print("Summary fits in a single embed")
        else:
            debug_print(f"Summary exceeds max embed length ({len(summary)} > {max_embed_description_length}), splitting into chunks")
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

            debug_print(f"Split summary into {len(summary_chunks)} chunks")

        # Send the first embed with the header
        # Nadpis je již součástí shrnutí, takže ho nemusíme přidávat do title
        first_embed = discord.Embed(
            description=summary_chunks[0],
            color=discord.Color.blue()
        )

        first_embed.set_footer(text=f"Celkem zpráv: {message_count}")
        first_embed.timestamp = datetime.now()

        debug_print("Sending first embed with header")
        try:
            await target_channel.send(embed=first_embed)
            debug_print("First embed sent successfully")

            # Send additional embeds if needed
            if len(summary_chunks) > 1:
                debug_print(f"Sending {len(summary_chunks) - 1} additional embeds")
                for i, chunk in enumerate(summary_chunks[1:], 1):
                    embed = discord.Embed(
                        description=chunk,
                        color=discord.Color.blue()
                    )

                    await target_channel.send(embed=embed)
                    debug_print(f"Sent chunk {i+1}/{len(summary_chunks)}")

            debug_print("All summary chunks sent successfully")
        except Exception as e:
            print(f"[Summary] Error sending summary to channel: {e}")
            debug_print(f"Error sending summary to channel: {str(e)}")
            debug_print(f"Exception type: {type(e).__name__}")
            debug_print(f"Exception traceback: {traceback.format_exc()}")

    @commands.command(name="sumarizace-souhrn")
    @commands.has_permissions(administrator=True)
    async def daily_summary_command(self, ctx, date_str: str = None, channel: discord.TextChannel = None):
        """Vygeneruje shrnutí chatu za celý den z databáze

        Parameters:
        -----------
        date_str: Datum ve formátu DD/MM/RRRR (výchozí: včerejší datum)
        channel: Volitelný kanál, kam poslat shrnutí
        """
        await ctx.send("Generuji shrnutí chatu...", ephemeral=True)
        debug_print(f"Command sumarizace-souhrn executed by {ctx.author.name} (ID: {ctx.author.id})")
        debug_print(f"Parameters: date_str={date_str}, channel={channel.name if channel else None}")

        # Get the date
        if date_str:
            # Convert from DD/MM/YYYY to YYYY-MM-DD
            date = chat_db.convert_date_format(date_str)
            debug_print(f"Converting date format from {date_str} to {date}")
            if not date:
                await ctx.send("Neplatný formát data. Použijte formát DD/MM/RRRR (např. 01/05/2024).", ephemeral=True)
                debug_print(f"Invalid date format: {date_str}")
                return
        else:
            # Default to yesterday
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            debug_print(f"No date provided, using yesterday: {date}")

        # Get messages for the specified date
        try:
            messages = chat_db.get_messages_by_date(date)
            print(f"[Summary] Daily summary command: Found {len(messages)} messages for {date}")
            debug_print(f"Retrieved {len(messages)} messages for date {date}")

            # Log a sample of messages
            sample_size = min(5, len(messages))
            print(f"[Summary] Sample of {sample_size} messages:")
            for i, msg in enumerate(messages[:sample_size]):
                username = msg.get("display_name") or msg.get("username", "Unknown")
                content = msg.get("content", "")
                print(f"[Summary]   Message {i+1}: {username}: {content[:100]}...")
        except Exception as e:
            print(f"[Summary] Error getting messages by date: {e}")
            debug_print(f"Error getting messages by date: {str(e)}")
            debug_print(f"Exception type: {type(e).__name__}")
            debug_print(f"Exception traceback: {traceback.format_exc()}")
            await ctx.send(f"Chyba při získávání zpráv: {e}", ephemeral=True)
            return

        if not messages:
            print(f"[Summary] Daily summary command: No messages found for {date}")
            debug_print(f"No messages found for date {date}")
            await ctx.send(f"Žádné zprávy pro {date} nebyly nalezeny.", ephemeral=True)
            return

        # Check if we already have a summary for this date
        existing_summary = chat_db.get_summary_by_date(date)
        if existing_summary:
            debug_print(f"Found existing summary for date {date}")
            debug_print(f"Existing summary info: message_count={existing_summary.get('message_count')}, manual={existing_summary.get('manual')}, auto_generated={existing_summary.get('auto_generated')}")

            # Ask if the user wants to regenerate
            await ctx.send(
                f"Pro datum {date} již existuje shrnutí. Chcete ho přegenerovat? (ano/ne)",
                ephemeral=True
            )

            # Wait for response
            try:
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["ano", "ne"]

                response = await self.bot.wait_for("message", check=check, timeout=30.0)
                debug_print(f"User response: {response.content}")

                if response.content.lower() == "ne":
                    await ctx.send("Operace zrušena.", ephemeral=True)
                    debug_print("Operation cancelled by user")
                    return

                # Delete the response message if possible
                try:
                    await response.delete()
                except Exception as e:
                    debug_print(f"Could not delete response message: {str(e)}")

            except asyncio.TimeoutError:
                await ctx.send("Čas na odpověď vypršel. Operace zrušena.", ephemeral=True)
                debug_print("Response timeout, operation cancelled")
                return

        # Generate summary
        debug_print(f"Generating summary for {date} with {len(messages)} messages")
        summary = await self.generate_summary(messages, date)

        if not summary:
            await ctx.send("Nepodařilo se vygenerovat shrnutí.", ephemeral=True)
            debug_print("Failed to generate summary")
            return

        debug_print(f"Summary generated successfully, length: {len(summary)} characters")
        debug_print(f"Summary preview (first 500 chars): {summary[:500]}...")

        # Extract message IDs from the summary for topic beginnings
        import re
        topic_links = re.findall(r'\[téma\]\(https://discord\.com/channels/\d+/\d+/(\d+)\)', summary)
        debug_print(f"Extracted {len(topic_links)} topic links from summary")

        if topic_links:
            print("[Summary] Topic links found:")
            for i, link in enumerate(topic_links):
                print(f"[Summary]   Topic {i+1}: Message ID {link}")

        # Save summary to database with message IDs for topics
        summary_data = {
            "date": date,
            "message_count": len(messages),
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "topic_message_ids": topic_links,
            "requested_by": str(ctx.author.id),
            "manual": True  # Mark as manually created
        }

        debug_print(f"Saving summary to database: {json.dumps(summary_data, ensure_ascii=False, default=str)[:500]}...")
        chat_db.save_summary(summary_data)
        debug_print("Summary saved to database successfully")

        # Get target channel ID
        target_channel_id = channel.id if channel else None
        debug_print(f"Target channel ID: {target_channel_id or 'default'}")

        # Send summary to channel
        debug_print("Sending summary to channel")
        await self.send_summary(summary_data, target_channel_id)
        debug_print("Summary sent successfully")

        # Format date for display (YYYY-MM-DD to DD/MM/YYYY)
        display_date = f"{date[8:10]}/{date[5:7]}/{date[0:4]}"

        # Prepare confirmation message
        if channel:
            await ctx.send(f"Shrnutí pro {display_date} bylo vygenerováno a odesláno do kanálu {channel.mention}.", ephemeral=True)
            debug_print(f"Summary for {display_date} sent to channel {channel.name}")
        else:
            await ctx.send(f"Shrnutí pro {display_date} bylo vygenerováno a odesláno do výchozího kanálu.", ephemeral=True)
            debug_print(f"Summary for {display_date} sent to default channel")

    @commands.command(name="sumarizace")
    @commands.cooldown(1, SUMMARY_COOLDOWN_HOURS*60*60, BucketType.user)  # 1 use per X hours per user
    async def user_summary(self, ctx, count: int = 100):
        """Vygeneruje shrnutí posledních N zpráv a pošle ho do soukromé zprávy

        Parameters:
        -----------
        count: Počet zpráv k sumarizaci (výchozí: 100, maximum: 500)
        """
        print(f"[Summary] Command sumarizace executed by {ctx.author.name} (ID: {ctx.author.id})")
        print(f"[Summary] Parameters: count={count}")

        # Check if count is within reasonable limits
        if count > 500:
            await ctx.send("Maximální počet zpráv pro sumarizaci je 500.", ephemeral=True)
            ctx.command.reset_cooldown(ctx)
            print(f"[Summary] Count {count} exceeds maximum limit (500), command cancelled")
            return

        if count < 10:
            await ctx.send("Minimální počet zpráv pro sumarizaci je 10.", ephemeral=True)
            ctx.command.reset_cooldown(ctx)
            print(f"[Summary] Count {count} is below minimum limit (10), command cancelled")
            return

        # Admin bypass for cooldown
        if ctx.author.guild_permissions.administrator:
            ctx.command.reset_cooldown(ctx)
            print(f"[Summary] Admin user {ctx.author.name} detected, cooldown bypassed")

        await ctx.send(f"Generuji shrnutí posledních {count} zpráv. Výsledek ti pošlu do soukromé zprávy.", ephemeral=True)

        try:
            # Get the latest messages
            print(f"[Summary] Retrieving latest {count} messages for user {ctx.author.display_name}")

            messages = chat_db.get_latest_messages(count)
            print(f"[Summary] User summary: Found {len(messages)} messages for user {ctx.author.display_name}")


            # Log a sample of messages
            sample_size = min(5, len(messages))
            print(f"[Summary] Sample of {sample_size} messages for user {ctx.author.display_name}:")
            for i, msg in enumerate(messages[:sample_size]):
                username = msg.get("display_name") or msg.get("username", "Unknown")
                content = msg.get("content", "")
                print(f"[Summary]   Message {i+1}: {username}: {content[:100]}...")

            if not messages:
                print(f"[Summary] No messages found for user {ctx.author.display_name}, command cancelled")
                await ctx.send("Nenalezeny žádné zprávy k sumarizaci.", ephemeral=True)

                return

            # Generate summary
            current_date = datetime.now().strftime("%Y-%m-%d")
            print(f"[Summary] User {ctx.author.name} requested summary for {len(messages)} messages")

            summary = await self.generate_summary(messages, current_date)

            if not summary:
                print(f"[Summary] Failed to generate summary for user {ctx.author.name}")
                await ctx.send("Nepodařilo se vygenerovat shrnutí.", ephemeral=True)

                return

            print(f"[Summary] Summary generated successfully for user {ctx.author.name}, length: {len(summary)} characters")
            print(f"[Summary] Summary preview (first 100 chars): {summary[:100]}...")

            # Extract message IDs from the summary for topic beginnings
            import re
            topic_links = re.findall(r'\[téma\]\(https://discord\.com/channels/\d+/\d+/(\d+)\)', summary)
            print(f"[Summary] Extracted {len(topic_links)} topic links from summary for user {ctx.author.display_name}")

            if topic_links:
                print(f"[Summary] Topic links found for user {ctx.author.display_name}:")
                for i, link in enumerate(topic_links):
                    print(f"[Summary]   Topic {i+1}: Message ID {link}")

            # Create summary data
            summary_data = {
                "date": current_date,
                "message_count": len(messages),
                "summary": summary,
                "timestamp": datetime.now().isoformat(),
                "topic_message_ids": topic_links,
                "requested_by": str(ctx.author.id),
                "manual": True  # Mark as manually created
            }

            print(f"[Summary] Created summary data for user {ctx.author.name} with {len(summary)} characters")

            # Send summary to user via DM
            print(f"[Summary] Sending summary to user {ctx.author.name} via DM")

            await self.send_summary_dm(ctx.author, summary_data)
            print(f"[Summary] Summary sent to user {ctx.author.name}'s DM successfully")


            # Confirm to the user
            await ctx.send("Shrnutí bylo vygenerováno a posláno do tvých soukromých zpráv.", ephemeral=True)
            print(f"[Summary] Command completed successfully for user {ctx.author.name}")


        except Exception as e:
            print(f"[Summary] Error generating user summary: {e}")

            await ctx.send(f"Chyba při generování shrnutí: {e}", ephemeral=True)
            # Don't reset cooldown on error to prevent abuse

    async def send_summary_dm(self, user, summary_data):
        """Send the summary to a user via DM"""
        print(f"[Summary] Preparing to send summary DM to user {user.name} (ID: {user.id})")


        # Create embed
        message_count = summary_data.get("message_count", 0)
        summary = summary_data.get("summary", "No summary available")
        print(f"[Summary] Preparing DM with summary length: {len(summary)} characters, message count: {message_count}")


        # Split summary into chunks if it's too long
        max_embed_description_length = 4096
        summary_chunks = []

        if len(summary) <= max_embed_description_length:
            summary_chunks = [summary]
            print(f"[Summary] Summary fits in a single embed for user {user.name}")
        else:
            print(f"[Summary] Summary exceeds max embed length ({len(summary)} > {max_embed_description_length}), splitting into chunks for user {user.name}")
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

            print(f"[Summary] Split summary into {len(summary_chunks)} chunks for user {user.name}")

        # Send the first embed with the header
        # Nadpis je již součástí shrnutí, takže ho nemusíme přidávat do title
        first_embed = discord.Embed(
            description=summary_chunks[0],
            color=discord.Color.blue()
        )

        first_embed.set_footer(text=f"Celkem zpráv: {message_count}")
        first_embed.timestamp = datetime.now()

        try:
            print(f"[Summary] Creating DM channel for user {user.name}")

            dm_channel = await user.create_dm()
            print(f"[Summary] Sending first embed with header to user {user.name}")

            await dm_channel.send(embed=first_embed)

            # Send additional embeds if needed
            if len(summary_chunks) > 1:
                print(f"[Summary] Sending {len(summary_chunks) - 1} additional embeds to user {user.name}")

                for i, chunk in enumerate(summary_chunks[1:], 1):
                    embed = discord.Embed(
                        description=chunk,
                        color=discord.Color.blue()
                    )

                    await dm_channel.send(embed=embed)
                    print(f"[Summary] Sent chunk {i+1}/{len(summary_chunks)} to user {user.name}")


            print(f"[Summary] Successfully sent all summary chunks to user {user.name}")

        except discord.Forbidden:
            # User has DMs disabled
            print(f"[Summary] Could not send DM to {user.display_name} - DMs disabled")

        except Exception as e:
            print(f"[Summary] Error sending summary DM: {e}")
            print(f"[Summary] Exception type: {type(e).__name__}")
            print(f"[Summary] Exception traceback: {traceback.format_exc()}")


    @commands.command(name="pocetzpravzaden")
    @commands.has_permissions(administrator=True)
    async def message_count_today(self, ctx):
        """Zobrazí počet zpráv v sumarizačním chatu za dnešní den (admin only)"""
        debug_print(f"Command pocetzpravzaden executed by {ctx.author.name} (ID: {ctx.author.id})")

        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        debug_print(f"Getting message count for today: {today}")

        # Get messages from today
        try:
            messages = chat_db.get_messages_by_date(today)
            message_count = len(messages)
            debug_print(f"Retrieved {message_count} messages for today")

            # Format date for display (YYYY-MM-DD to DD/MM/YYYY)
            display_date = f"{today[8:10]}/{today[5:7]}/{today[0:4]}"
            debug_print(f"Formatted date for display: {display_date}")

            # Create embed
            embed = discord.Embed(
                title=f"📊 Statistika zpráv za {display_date}",
                description=f"V sumarizačním chatu bylo dnes odesláno **{message_count}** zpráv.",
                color=discord.Color.blue()
            )

            embed.set_footer(text=f"Kanál: {CHAT_ID}")
            embed.timestamp = datetime.now()
            debug_print("Created embed with message count statistics")

            await ctx.send(embed=embed, ephemeral=True)
            debug_print("Sent message count statistics to user")

        except Exception as e:
            print(f"[Summary] Error getting message count for today: {e}")
            debug_print(f"Error getting message count for today: {str(e)}")
            debug_print(f"Exception type: {type(e).__name__}")
            debug_print(f"Exception traceback: {traceback.format_exc()}")
            await ctx.send(f"Chyba při získávání počtu zpráv: {e}", ephemeral=True)

    @user_summary.error
    async def user_summary_error(self, ctx, error):
        """Handle errors for the user_summary command"""
        debug_print(f"Error in user_summary command: {str(error)}")
        debug_print(f"Error type: {type(error).__name__}")

        if isinstance(error, CommandOnCooldown):
            minutes, seconds = divmod(int(error.retry_after), 60)
            hours, minutes = divmod(minutes, 60)
            debug_print(f"Command on cooldown. Retry after: {hours}h {minutes}m {seconds}s")

            if hours > 0:
                message = (
                    f"Tento příkaz můžeš použít pouze jednou za {SUMMARY_COOLDOWN_HOURS} hodin. "
                    f"Zkus to znovu za {hours} hodin a {minutes} minut."
                )
                await ctx.send(message, ephemeral=True)
                debug_print(f"Sent cooldown message (hours): {message}")
            elif minutes > 0:
                message = (
                    f"Tento příkaz můžeš použít pouze jednou za {SUMMARY_COOLDOWN_HOURS} hodin. "
                    f"Zkus to znovu za {minutes} minut a {seconds} sekund."
                )
                await ctx.send(message, ephemeral=True)
                debug_print(f"Sent cooldown message (minutes): {message}")
            else:
                message = (
                    f"Tento příkaz můžeš použít pouze jednou za {SUMMARY_COOLDOWN_HOURS} hodin. "
                    f"Zkus to znovu za {seconds} sekund."
                )
                await ctx.send(message, ephemeral=True)
                debug_print(f"Sent cooldown message (seconds): {message}")
        else:
            debug_print(f"Unhandled error: {str(error)}")
            debug_print(f"Exception traceback: {traceback.format_exc()}")
            await ctx.send(f"Nastala chyba: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChatSummary(bot))