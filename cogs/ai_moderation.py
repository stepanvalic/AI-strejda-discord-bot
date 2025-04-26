import os
import json
import discord
import asyncio
import datetime
import google.generativeai as genai
from discord.ext import commands, tasks
from utils import config

# Load configuration
GEMINI_API_KEY = config.get('GEMINI_API_KEY')
AI_MODEL = config.get('AI_MODEL', 'gemini-2.0-flash')
# Message batch size
AI_MESSAGES_BATCH = config.get_int('AI_MESSAGES_BATCH')
if not AI_MESSAGES_BATCH:
    print("[AI Mod] ERROR: AI_MESSAGES_BATCH not set in configuration. AI moderation will not function properly.")
    AI_MESSAGES_BATCH = 0  # Will prevent processing
else:
    print(f"[AI Mod] Using batch size of {AI_MESSAGES_BATCH} messages")

AI_MODERATION_SAVE_FILE = config.get('AI_MODERATION_SAVE_FILE', 'db/ai_moderation.json')
AI_MODERATION_INTERVAL_MINUTES = config.get_int('AI_MODERATION_INTERVAL_MINUTES', 5)

# Channel IDs where moderation should be active
AI_MODERATION_CHANNEL_IDS = config.get('AI_MODERATION_CHANNEL_IDS', [])
# Convert to integers if provided as strings
if AI_MODERATION_CHANNEL_IDS:
    try:
        AI_MODERATION_CHANNEL_IDS = [int(channel_id) if isinstance(channel_id, str) else channel_id for channel_id in AI_MODERATION_CHANNEL_IDS]
        print(f"[AI Mod] Moderation active in {len(AI_MODERATION_CHANNEL_IDS)} channels: {AI_MODERATION_CHANNEL_IDS}")
    except (ValueError, TypeError) as e:
        print(f"[AI Mod] Error parsing AI_MODERATION_CHANNEL_IDS: {e}")
        AI_MODERATION_CHANNEL_IDS = []
else:
    print("[AI Mod] No channel restrictions set. Moderation will be active in all channels.")

# Positive thresholds
AI_POSITIVE_THRESHOLD_1 = config.get_int('AI_POSITIVE_THRESHOLD_1', 800)
AI_POSITIVE_THRESHOLD_2 = config.get_int('AI_POSITIVE_THRESHOLD_2', 2000)
AI_POSITIVE_THRESHOLD_3 = config.get_int('AI_POSITIVE_THRESHOLD_3', 5000)

# Negative thresholds
AI_NEGATIVE_THRESHOLD = config.get_int('AI_NEGATIVE_THRESHOLD', -30)
AI_VERY_NEGATIVE_THRESHOLD = config.get_int('AI_VERY_NEGATIVE_THRESHOLD', -1000)

# Penalty for very negative messages
AI_NEGATIVE_PENALTY = config.get_int('AI_NEGATIVE_PENALTY', -50)

# Role IDs
AI_POSITIVE_ROLE_ID_1 = config.get('AI_POSITIVE_ROLE_ID_1')
AI_POSITIVE_ROLE_ID_2 = config.get('AI_POSITIVE_ROLE_ID_2')
AI_POSITIVE_ROLE_ID_3 = config.get('AI_POSITIVE_ROLE_ID_3')
AI_NEGATIVE_ROLE_ID = config.get('AI_NEGATIVE_ROLE_ID')

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Convert role IDs to int if provided
try:
    AI_POSITIVE_ROLE_ID_1 = int(AI_POSITIVE_ROLE_ID_1) if AI_POSITIVE_ROLE_ID_1 else None
except ValueError:
    AI_POSITIVE_ROLE_ID_1 = None
    print("Warning: Invalid AI_POSITIVE_ROLE_ID_1 in .env file")

try:
    AI_POSITIVE_ROLE_ID_2 = int(AI_POSITIVE_ROLE_ID_2) if AI_POSITIVE_ROLE_ID_2 else None
except ValueError:
    AI_POSITIVE_ROLE_ID_2 = None
    print("Warning: Invalid AI_POSITIVE_ROLE_ID_2 in .env file")

try:
    AI_POSITIVE_ROLE_ID_3 = int(AI_POSITIVE_ROLE_ID_3) if AI_POSITIVE_ROLE_ID_3 else None
except ValueError:
    AI_POSITIVE_ROLE_ID_3 = None
    print("Warning: Invalid AI_POSITIVE_ROLE_ID_3 in .env file")

try:
    AI_NEGATIVE_ROLE_ID = int(AI_NEGATIVE_ROLE_ID) if AI_NEGATIVE_ROLE_ID else None
except ValueError:
    AI_NEGATIVE_ROLE_ID = None
    print("Warning: Invalid AI_NEGATIVE_ROLE_ID in .env file")

class AIModeration(commands.Cog):
    def __init__(self, bot):
        # Get the batch size from config
        global AI_MESSAGES_BATCH
        AI_MESSAGES_BATCH = config.get_int('AI_MESSAGES_BATCH')
        print(f"[AI Mod] Initialized with batch size of {AI_MESSAGES_BATCH} messages")

        self.bot = bot
        self.pending_messages = {}  # {user_id: [messages]}
        self.data = self.load_data()
        self.process_messages.start()

    def cog_unload(self):
        self.process_messages.cancel()

    def load_data(self):
        """Load AI moderation data from JSON file"""
        os.makedirs(os.path.dirname(AI_MODERATION_SAVE_FILE), exist_ok=True)

        if not os.path.exists(AI_MODERATION_SAVE_FILE):
            default_data = {
                "users": {},
                "last_updated": None
            }
            with open(AI_MODERATION_SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)
            return default_data

        try:
            with open(AI_MODERATION_SAVE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {
                "users": {},
                "last_updated": None
            }

    def save_data(self):
        """Save AI moderation data to JSON file"""
        self.data["last_updated"] = datetime.datetime.now().isoformat()
        with open(AI_MODERATION_SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def get_user_data(self, user_id):
        """Get user data from the database, create if not exists"""
        user_id = str(user_id)

        if user_id not in self.data["users"]:
            self.data["users"][user_id] = {
                "username": None,
                "positive_score": 0,
                "negative_score": 0,
                "total_score": 0,
                "messages_analyzed": 0,
                "last_analyzed": None,
                "timeout_count": 0,
                "last_timeout": None,
                "has_positive_role_1": False,
                "has_positive_role_2": False,
                "has_positive_role_3": False,
                "has_negative_role": False,
                "last_role_update_1": None,
                "last_role_update_2": None,
                "last_role_update_3": None,
                "last_negative_role_update": None
            }

        return self.data["users"][user_id]

    def update_user_data(self, user_id, username, positive_delta=0, negative_delta=0):
        """Update user data with new scores"""
        user_id = str(user_id)
        user_data = self.get_user_data(user_id)

        # Update username
        user_data["username"] = username

        # Apply penalty for very negative messages
        if negative_delta > 90:  # If message is very negative (increased threshold from 80 to 90)
            print(f"[AI Mod] Applying extra penalty of {AI_NEGATIVE_PENALTY} for very negative message")
            negative_delta += abs(AI_NEGATIVE_PENALTY)  # Add extra penalty

        # Update scores
        user_data["positive_score"] += positive_delta
        user_data["negative_score"] += negative_delta
        user_data["total_score"] = user_data["positive_score"] - user_data["negative_score"]
        user_data["messages_analyzed"] += 1
        user_data["last_analyzed"] = datetime.datetime.now().isoformat()

        self.save_data()
        return user_data

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages and add them to the pending queue"""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return

        # Ignore příkazy (zprávy začínající !) a odkazy
        if message.content.startswith('!') or 'http://' in message.content or 'https://' in message.content:
            return

        # Check if moderation is enabled for this channel
        if AI_MODERATION_CHANNEL_IDS and message.channel.id not in AI_MODERATION_CHANNEL_IDS:
            # Skip messages from channels not in the allowed list
            return

        # Add message to pending queue
        user_id = message.author.id
        if user_id not in self.pending_messages:
            self.pending_messages[user_id] = []
            print(f"[AI Mod] New user added to tracking: {message.author.display_name} (ID: {user_id})")

        # Store relevant message data
        self.pending_messages[user_id].append({
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "channel_id": message.channel.id,
            "message_id": message.id
        })

        print(f"[AI Mod] Message recorded for {message.author.display_name}: {len(self.pending_messages[user_id])}/{AI_MESSAGES_BATCH} messages")

        # Keep only the latest AI_MESSAGES_BATCH messages
        if len(self.pending_messages[user_id]) > AI_MESSAGES_BATCH:
            self.pending_messages[user_id] = self.pending_messages[user_id][-AI_MESSAGES_BATCH:]
            print(f"[AI Mod] Message batch full for {message.author.display_name}, ready for analysis")

        # Process messages immediately when we reach the batch size
        if len(self.pending_messages[user_id]) >= AI_MESSAGES_BATCH:
            print(f"[AI Mod] Reached {AI_MESSAGES_BATCH} messages for {message.author.display_name}, processing now...")
            # Ensure we only process the exact batch size
            self.pending_messages[user_id] = self.pending_messages[user_id][-AI_MESSAGES_BATCH:]
            await self.process_user_messages(user_id)

    async def analyze_sentiment(self, messages):
        """Analyze sentiment of messages using Google Gemini API"""
        if not GEMINI_API_KEY:
            print("[AI Mod] Google Gemini API key is missing")
            return None

        if not messages:
            print("[AI Mod] No messages to analyze")
            return None

        # Combine messages into a single text for analysis
        combined_text = "\n".join([msg["content"] for msg in messages])
        print(f"[AI Mod] Analyzing {len(messages)} messages with total length of {len(combined_text)} characters")

        # Prepare prompt for sentiment analysis
        prompt = f"""Analyze the sentiment of the following messages from a Discord user.
Rate the overall sentiment on a scale from -100 (extremely negative/toxic) to +100 (extremely positive/friendly).
Be lenient in your analysis and give users the benefit of the doubt.
Positive sentiment should be weighted more than negative sentiment.
Only rate messages as very negative if they are clearly toxic, harmful, or offensive.

Messages:
{combined_text}

Provide your analysis in the following JSON format:
{{
  "sentiment_score": <number between -100 and 100>,
  "positive_score": <number between 0 and 100>,
  "negative_score": <number between 0 and 100>,
  "explanation": "<brief explanation of your rating>"
}}
"""

        try:
            print(f"[AI Mod] Creating Gemini model instance with model: {AI_MODEL}")
            # Create a Gemini model instance
            model = genai.GenerativeModel(AI_MODEL)

            # Configure response format to be JSON
            generation_config = genai.types.GenerationConfig(
                response_mime_type='application/json'
            )

            print("[AI Mod] Calling Gemini API...")
            # Call the Gemini API
            response = await asyncio.to_thread(
                model.generate_content,
                [
                    "You are an AI assistant that analyzes the sentiment of Discord messages. You detect toxic, negative, neutral, and positive content. Be extremely lenient and charitable in your analysis. Give users the benefit of the doubt and focus much more on positive aspects of messages than negative ones. Only flag content as very negative if it's clearly harmful, offensive, or toxic. Avoid penalizing users for casual banter, jokes, or mild criticism. Assume good intentions whenever possible. Your goal is to create a positive community atmosphere while only flagging truly problematic content.",
                    prompt
                ],
                generation_config=generation_config
            )

            print("[AI Mod] Received response from Gemini API")
            # Parse the response
            if response.text:
                try:
                    result = json.loads(response.text)
                    print(f"[AI Mod] Successfully parsed JSON response: {result}")
                    return result
                except json.JSONDecodeError:
                    print(f"[AI Mod] Failed to parse JSON response: {response.text}")
                    return None
            else:
                print("[AI Mod] Empty response from Gemini API")
                return None

        except Exception as e:
            print(f"[AI Mod] Error calling Google Gemini API: {e}")
            return None

    async def process_user_messages(self, user_id):
        """Process messages for a specific user"""
        if not self.bot.is_ready():
            print(f"[AI Mod] Bot not ready, skipping message processing for user {user_id}")
            return

        user_id = int(user_id)  # Ensure user_id is an integer
        if user_id not in self.pending_messages or not self.pending_messages[user_id]:
            print(f"[AI Mod] No messages to process for user {user_id}")
            return

        messages = self.pending_messages[user_id]
        if len(messages) < 3:  # Skip if too few messages
            print(f"[AI Mod] Skipping user {user_id}: Not enough messages ({len(messages)}/3 minimum)")
            return

        # Get user
        guild = self.bot.guilds[0]  # Assuming bot is in only one guild
        member = guild.get_member(user_id)
        if not member:
            print(f"[AI Mod] Skipping user {user_id}: Member not found in guild")
            return

        # Note if user is admin (for logging purposes)
        is_admin = member.guild_permissions.administrator
        if is_admin:
            print(f"[AI Mod] User {member.display_name} is admin - will analyze but not apply actions")

        print(f"[AI Mod] Analyzing sentiment for {member.display_name} ({len(messages)} messages)")

        # Analyze sentiment
        result = await self.analyze_sentiment(messages)
        if not result:
            print(f"[AI Mod] Failed to analyze sentiment for {member.display_name}")
            return

        # Update user data
        positive_score = result.get("positive_score", 0)
        negative_score = result.get("negative_score", 0)
        sentiment_score = result.get("sentiment_score", 0)
        explanation = result.get("explanation", "No explanation provided")

        print(f"[AI Mod] Analysis for {member.display_name}: Sentiment={sentiment_score}, Positive={positive_score}, Negative={negative_score}")
        print(f"[AI Mod] Explanation: {explanation}")

        user_data = self.update_user_data(
            str(user_id),
            member.display_name,
            positive_delta=positive_score,
            negative_delta=negative_score
        )

        print(f"[AI Mod] Updated score for {member.display_name}: Total={user_data['total_score']}, Positive={user_data['positive_score']}, Negative={user_data['negative_score']}")

        # Clear processed messages
        self.pending_messages[user_id] = []
        print(f"[AI Mod] Cleared message batch for {member.display_name}")

        # Check for actions based on scores (skip actions for admins)
        if not is_admin:
            await self.check_user_actions(member, user_data)
        else:
            print(f"[AI Mod] Skipping actions for admin {member.display_name}")

    @tasks.loop(minutes=AI_MODERATION_INTERVAL_MINUTES)
    async def process_messages(self):
        """Process pending messages at regular intervals"""
        if not self.bot.is_ready():
            print("[AI Mod] Bot not ready, skipping message processing")
            return

        if not self.pending_messages:
            print("[AI Mod] No pending messages to process")
            return

        print(f"[AI Mod] Processing messages for {len(self.pending_messages)} users")

        for user_id in list(self.pending_messages.keys()):
            await self.process_user_messages(user_id)

    async def check_user_actions(self, member, user_data):
        """Check if any actions need to be taken based on user scores"""
        # Negative threshold check is disabled - no notifications or timeouts
        # Just log the information for debugging purposes
        if user_data["total_score"] <= AI_NEGATIVE_THRESHOLD:
            print(f"[AI Mod] User {member.display_name} has negative score ({user_data['total_score']}), but notifications are disabled")

        # Check for very negative role (-1000 points)
        if AI_NEGATIVE_ROLE_ID and user_data["total_score"] <= AI_VERY_NEGATIVE_THRESHOLD:
            if not user_data.get("has_negative_role", False):
                print(f"[AI Mod] User {member.display_name} has very negative score ({user_data['total_score']}), adding negative role")
                try:
                    # Add negative role
                    role = member.guild.get_role(AI_NEGATIVE_ROLE_ID)
                    if role:
                        await member.add_roles(role, reason=f"AI Moderation: Very negative sentiment score ({user_data['total_score']})")

                        # Update user data
                        user_data["has_negative_role"] = True
                        user_data["last_negative_role_update"] = datetime.datetime.now().isoformat()
                        self.save_data()
                        print(f"[AI Mod] Added negative role to {member.display_name}")
                except Exception as e:
                    print(f"[AI Mod] Error adding negative role to {member.display_name}: {e}")
        elif AI_NEGATIVE_ROLE_ID and user_data.get("has_negative_role", False) and user_data["total_score"] > AI_VERY_NEGATIVE_THRESHOLD:
            print(f"[AI Mod] User {member.display_name}'s score improved above very negative threshold ({user_data['total_score']}), removing negative role")
            try:
                # Remove negative role if score improves
                role = member.guild.get_role(AI_NEGATIVE_ROLE_ID)
                if role and role in member.roles:
                    await member.remove_roles(role, reason=f"AI Moderation: Score improved above very negative threshold ({user_data['total_score']})")

                    # Update user data
                    user_data["has_negative_role"] = False
                    user_data["last_negative_role_update"] = datetime.datetime.now().isoformat()
                    self.save_data()
                    print(f"[AI Mod] Removed negative role from {member.display_name}")
            except Exception as e:
                print(f"[AI Mod] Error removing negative role from {member.display_name}: {e}")

        # Check for positive roles (multiple levels)
        # Level 3 (5000+ points)
        if AI_POSITIVE_ROLE_ID_3 and user_data["total_score"] >= AI_POSITIVE_THRESHOLD_3:
            if not user_data.get("has_positive_role_3", False):
                print(f"[AI Mod] User {member.display_name} has reached level 3 positive score ({user_data['total_score']}), adding level 3 role")
                try:
                    # Add level 3 positive role
                    role = member.guild.get_role(AI_POSITIVE_ROLE_ID_3)
                    if role:
                        await member.add_roles(role, reason=f"AI Moderation: Level 3 positive score ({user_data['total_score']})")

                        # Update user data
                        user_data["has_positive_role_3"] = True
                        user_data["last_role_update_3"] = datetime.datetime.now().isoformat()
                        self.save_data()
                        print(f"[AI Mod] Added level 3 positive role to {member.display_name}")

                        # Send DM to user
                        try:
                            embed = discord.Embed(
                                title="🌟🌟🌟 Odměna za vynikající chování",
                                description=f"Byla ti udělena role **{role.name}** za vynikající pozitivní chování na serveru!",
                                color=discord.Color.gold()
                            )
                            embed.add_field(
                                name="Skóre",
                                value=f"Tvoje skóre: **{user_data['total_score']}**\n"
                                      f"Hranice pro nejvyšší odměnu: **{AI_POSITIVE_THRESHOLD_3}**"
                            )
                            embed.add_field(
                                name="Co to znamená?",
                                value="Náš AI systém detekoval mimořádně pozitivní chování ve tvých zprávách. "
                                      "Děkujeme, že jsi vzorem pro ostatní členy serveru!"
                            )
                            embed.set_footer(text="Toto je automatická zpráva od AI moderačního systému.")

                            await member.send(embed=embed)
                            print(f"[AI Mod] DM sent to {member.display_name} about level 3 positive role")
                        except discord.Forbidden:
                            print(f"[AI Mod] Could not send DM to {member.display_name} (DMs disabled)")
                except Exception as e:
                    print(f"[AI Mod] Error adding level 3 positive role to {member.display_name}: {e}")
        elif AI_POSITIVE_ROLE_ID_3 and user_data.get("has_positive_role_3", False) and user_data["total_score"] < AI_POSITIVE_THRESHOLD_3:
            print(f"[AI Mod] User {member.display_name}'s score dropped below level 3 threshold ({user_data['total_score']}), removing level 3 role")
            try:
                # Remove level 3 role if score drops
                role = member.guild.get_role(AI_POSITIVE_ROLE_ID_3)
                if role and role in member.roles:
                    await member.remove_roles(role, reason=f"AI Moderation: Score dropped below level 3 threshold ({user_data['total_score']})")

                    # Update user data
                    user_data["has_positive_role_3"] = False
                    user_data["last_role_update_3"] = datetime.datetime.now().isoformat()
                    self.save_data()
                    print(f"[AI Mod] Removed level 3 positive role from {member.display_name}")
            except Exception as e:
                print(f"[AI Mod] Error removing level 3 positive role from {member.display_name}: {e}")

        # Level 2 (2000+ points)
        if AI_POSITIVE_ROLE_ID_2 and user_data["total_score"] >= AI_POSITIVE_THRESHOLD_2:
            if not user_data.get("has_positive_role_2", False):
                print(f"[AI Mod] User {member.display_name} has reached level 2 positive score ({user_data['total_score']}), adding level 2 role")
                try:
                    # Add level 2 positive role
                    role = member.guild.get_role(AI_POSITIVE_ROLE_ID_2)
                    if role:
                        await member.add_roles(role, reason=f"AI Moderation: Level 2 positive score ({user_data['total_score']})")

                        # Update user data
                        user_data["has_positive_role_2"] = True
                        user_data["last_role_update_2"] = datetime.datetime.now().isoformat()
                        self.save_data()
                        print(f"[AI Mod] Added level 2 positive role to {member.display_name}")

                        # Send DM to user
                        try:
                            embed = discord.Embed(
                                title="🌟🌟 Odměna za výborné chování",
                                description=f"Byla ti udělena role **{role.name}** za výborné pozitivní chování na serveru!",
                                color=discord.Color.gold()
                            )
                            embed.add_field(
                                name="Skóre",
                                value=f"Tvoje skóre: **{user_data['total_score']}**\n"
                                      f"Hranice pro vyšší odměnu: **{AI_POSITIVE_THRESHOLD_2}**"
                            )
                            embed.add_field(
                                name="Co to znamená?",
                                value="Náš AI systém detekoval velmi pozitivní chování ve tvých zprávách. "
                                      "Děkujeme, že vytváříš příjemnou atmosféru na serveru!"
                            )
                            embed.set_footer(text="Toto je automatická zpráva od AI moderačního systému.")

                            await member.send(embed=embed)
                            print(f"[AI Mod] DM sent to {member.display_name} about level 2 positive role")
                        except discord.Forbidden:
                            print(f"[AI Mod] Could not send DM to {member.display_name} (DMs disabled)")
                except Exception as e:
                    print(f"[AI Mod] Error adding level 2 positive role to {member.display_name}: {e}")
        elif AI_POSITIVE_ROLE_ID_2 and user_data.get("has_positive_role_2", False) and user_data["total_score"] < AI_POSITIVE_THRESHOLD_2:
            print(f"[AI Mod] User {member.display_name}'s score dropped below level 2 threshold ({user_data['total_score']}), removing level 2 role")
            try:
                # Remove level 2 role if score drops
                role = member.guild.get_role(AI_POSITIVE_ROLE_ID_2)
                if role and role in member.roles:
                    await member.remove_roles(role, reason=f"AI Moderation: Score dropped below level 2 threshold ({user_data['total_score']})")

                    # Update user data
                    user_data["has_positive_role_2"] = False
                    user_data["last_role_update_2"] = datetime.datetime.now().isoformat()
                    self.save_data()
                    print(f"[AI Mod] Removed level 2 positive role from {member.display_name}")
            except Exception as e:
                print(f"[AI Mod] Error removing level 2 positive role from {member.display_name}: {e}")

        # Level 1 (800+ points)
        if AI_POSITIVE_ROLE_ID_1 and user_data["total_score"] >= AI_POSITIVE_THRESHOLD_1:
            if not user_data.get("has_positive_role_1", False):
                print(f"[AI Mod] User {member.display_name} has reached level 1 positive score ({user_data['total_score']}), adding level 1 role")
                try:
                    # Add level 1 positive role
                    role = member.guild.get_role(AI_POSITIVE_ROLE_ID_1)
                    if role:
                        await member.add_roles(role, reason=f"AI Moderation: Level 1 positive score ({user_data['total_score']})")

                        # Update user data
                        user_data["has_positive_role_1"] = True
                        user_data["last_role_update_1"] = datetime.datetime.now().isoformat()
                        self.save_data()
                        print(f"[AI Mod] Added level 1 positive role to {member.display_name}")

                        # Send DM to user
                        try:
                            embed = discord.Embed(
                                title="🌟 Odměna za pozitivní chování",
                                description=f"Byla ti udělena role **{role.name}** za pozitivní chování na serveru!",
                                color=discord.Color.gold()
                            )
                            embed.add_field(
                                name="Skóre",
                                value=f"Tvoje skóre: **{user_data['total_score']}**\n"
                                      f"Hranice pro odměnu: **{AI_POSITIVE_THRESHOLD_1}**"
                            )
                            embed.add_field(
                                name="Co to znamená?",
                                value="Náš AI systém detekoval pozitivní chování ve tvých zprávách. "
                                      "Děkujeme, že přispíváš k příjemné atmosféře na serveru!"
                            )
                            embed.set_footer(text="Toto je automatická zpráva od AI moderačního systému.")

                            await member.send(embed=embed)
                            print(f"[AI Mod] DM sent to {member.display_name} about level 1 positive role")
                        except discord.Forbidden:
                            print(f"[AI Mod] Could not send DM to {member.display_name} (DMs disabled)")
                except Exception as e:
                    print(f"[AI Mod] Error adding level 1 positive role to {member.display_name}: {e}")
        elif AI_POSITIVE_ROLE_ID_1 and user_data.get("has_positive_role_1", False) and user_data["total_score"] < AI_POSITIVE_THRESHOLD_1:
            print(f"[AI Mod] User {member.display_name}'s score dropped below level 1 threshold ({user_data['total_score']}), removing level 1 role")
            try:
                # Remove level 1 role if score drops
                role = member.guild.get_role(AI_POSITIVE_ROLE_ID_1)
                if role and role in member.roles:
                    await member.remove_roles(role, reason=f"AI Moderation: Score dropped below level 1 threshold ({user_data['total_score']})")

                    # Update user data
                    user_data["has_positive_role_1"] = False
                    user_data["last_role_update_1"] = datetime.datetime.now().isoformat()
                    self.save_data()
                    print(f"[AI Mod] Removed level 1 positive role from {member.display_name}")
            except Exception as e:
                print(f"[AI Mod] Error removing level 1 positive role from {member.display_name}: {e}")

    @process_messages.before_loop
    async def before_process_messages(self):
        await self.bot.wait_until_ready()

    @commands.command(name="aiscore")
    async def check_ai_score(self, ctx, member: discord.Member = None):
        """Zobrazí AI skóre uživatele"""
        target = member or ctx.author
        user_id = str(target.id)

        # Get user data
        user_data = self.get_user_data(user_id)

        # Create embed
        embed = discord.Embed(
            title=f"AI Skóre - {target.display_name}",
            description="Hodnocení chování na základě analýzy zpráv pomocí AI.",
            color=discord.Color.blue()
        )

        # Add score fields
        embed.add_field(
            name="Celkové skóre",
            value=f"**{user_data['total_score']}**",
            inline=False
        )

        embed.add_field(
            name="Pozitivní body",
            value=f"**{user_data['positive_score']}**",
            inline=True
        )

        embed.add_field(
            name="Negativní body",
            value=f"**{user_data['negative_score']}**",
            inline=True
        )

        embed.add_field(
            name="Analyzovaných zpráv",
            value=f"**{user_data['messages_analyzed']}**",
            inline=True
        )

        # Add thresholds
        embed.add_field(
            name="Hranice pro role",
            value=f"🌟 Úroveň 1: **{AI_POSITIVE_THRESHOLD_1}**\n"
                  f"🌟🌟 Úroveň 2: **{AI_POSITIVE_THRESHOLD_2}**\n"
                  f"🌟🌟🌟 Úroveň 3: **{AI_POSITIVE_THRESHOLD_3}**",
            inline=False
        )

        # Add negative thresholds
        embed.add_field(
            name="Negativní hranice",
            value=f"⚠️ Upozornění moderátorům: **{AI_NEGATIVE_THRESHOLD}**\n"
                  f"⛔ Negativní role: **{AI_VERY_NEGATIVE_THRESHOLD}**",
            inline=False
        )

        # Add timeout info if applicable
        if user_data["timeout_count"] > 0:
            embed.add_field(
                name="Timeouty",
                value=f"Počet: **{user_data['timeout_count']}**\n"
                      f"Poslední: {user_data['last_timeout'] and discord.utils.format_dt(datetime.datetime.fromisoformat(user_data['last_timeout']), 'R') or 'Nikdy'}",
                inline=False
            )

        # Add footer
        embed.set_footer(text="AI moderační systém")
        embed.timestamp = datetime.datetime.now()

        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="aitop")
    async def ai_top_users(self, ctx):
        """Zobrazí žebříček uživatelů podle AI skóre"""
        if not self.data["users"]:
            await ctx.send("Zatím nejsou k dispozici žádné statistiky AI moderace.", ephemeral=True)
            return

        # Sort users by total score (descending)
        sorted_users = sorted(
            self.data["users"].items(),
            key=lambda x: x[1]["total_score"],
            reverse=True
        )

        # Take top 10
        top_users = sorted_users[:10]

        # Create embed
        embed = discord.Embed(
            title="🏆 AI Skóre - Top 10 uživatelů",
            description="Žebříček uživatelů s nejvyšším AI skóre",
            color=discord.Color.gold()
        )

        # Add user fields
        for i, (user_id, data) in enumerate(top_users, 1):
            # Získání objektu uživatele z Discord serveru
            guild = ctx.guild
            member = guild.get_member(int(user_id))

            if member:
                # Použij jméno uživatele, pokud je uživatel na serveru
                user_display = member.display_name
            else:
                # Použij uložené jméno nebo "Neznámý uživatel", pokud uživatel není na serveru
                user_display = data["username"] or "Neznámý uživatel"

            embed.add_field(
                name=f"{i}. {user_display}",
                value=f"Skóre: **{data['total_score']}**\n"
                      f"Pozitivní: **{data['positive_score']}**\n"
                      f"Negativní: **{data['negative_score']}**",
                inline=True
            )

            # Add empty field every 2 entries for better formatting
            if i % 2 == 0 and i < len(top_users):
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Add footer
        embed.set_footer(text="AI moderační systém")
        embed.timestamp = datetime.datetime.now()

        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="aibottom")
    async def ai_bottom_users(self, ctx):
        """Zobrazí žebříček uživatelů s nejnižším AI skóre"""
        if not self.data["users"]:
            await ctx.send("Zatím nejsou k dispozici žádné statistiky AI moderace.", ephemeral=True)
            return

        # Sort users by total score (ascending)
        sorted_users = sorted(
            self.data["users"].items(),
            key=lambda x: x[1]["total_score"]
        )

        # Take bottom 10
        bottom_users = sorted_users[:10]

        # Create embed
        embed = discord.Embed(
            title="⚠️ AI Skóre - Nejhorších 10 uživatelů",
            description="Žebříček uživatelů s nejnižším AI skóre",
            color=discord.Color.red()
        )

        # Add user fields
        for i, (user_id, data) in enumerate(bottom_users, 1):
            # Získání objektu uživatele z Discord serveru
            guild = ctx.guild
            member = guild.get_member(int(user_id))

            if member:
                # Použij jméno uživatele, pokud je uživatel na serveru
                user_display = member.display_name
            else:
                # Použij uložené jméno nebo "Neznámý uživatel", pokud uživatel není na serveru
                user_display = data["username"] or "Neznámý uživatel"

            embed.add_field(
                name=f"{i}. {user_display}",
                value=f"Skóre: **{data['total_score']}**\n"
                      f"Pozitivní: **{data['positive_score']}**\n"
                      f"Negativní: **{data['negative_score']}**",
                inline=True
            )

            # Add empty field every 2 entries for better formatting
            if i % 2 == 0 and i < len(bottom_users):
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Add footer
        embed.set_footer(text="AI moderační systém")
        embed.timestamp = datetime.datetime.now()

        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="aicheck")
    @commands.has_permissions(administrator=True)
    async def ai_check_roles(self, ctx):
        """Zkontroluje a opraví role všech členů podle jejich AI skóre (admin only)"""
        # Informovat o zahájení kontroly
        status_message = await ctx.send("⏳ Zahajuji kontrolu rolí všech členů podle AI skóre...")

        # Statistiky
        stats = {
            "checked": 0,
            "no_score": 0,
            "roles_added": 0,
            "roles_removed": 0,
            "members_updated": 0,
            "errors": 0
        }

        # Role k ověření
        roles_to_check = []
        if AI_POSITIVE_ROLE_ID_1:
            roles_to_check.append((AI_POSITIVE_ROLE_ID_1, "level 1 positive", AI_POSITIVE_THRESHOLD_1, "has_positive_role_1"))
        if AI_POSITIVE_ROLE_ID_2:
            roles_to_check.append((AI_POSITIVE_ROLE_ID_2, "level 2 positive", AI_POSITIVE_THRESHOLD_2, "has_positive_role_2"))
        if AI_POSITIVE_ROLE_ID_3:
            roles_to_check.append((AI_POSITIVE_ROLE_ID_3, "level 3 positive", AI_POSITIVE_THRESHOLD_3, "has_positive_role_3"))
        if AI_NEGATIVE_ROLE_ID:
            roles_to_check.append((AI_NEGATIVE_ROLE_ID, "negative", AI_VERY_NEGATIVE_THRESHOLD, "has_negative_role"))

        # Získat všechny členy serveru
        members = ctx.guild.members
        total_members = len(members)

        # Aktualizovat zprávu o stavu
        await status_message.edit(content=f"⏳ Kontroluji role pro {total_members} členů...")

        # Projít všechny členy
        for i, member in enumerate(members):
            # Přeskočit boty
            if member.bot:
                continue

            # Přeskočit administrátory (neaplikujeme na ně role)
            if member.guild_permissions.administrator:
                continue

            stats["checked"] += 1

            # Získat data uživatele
            user_id = str(member.id)
            if user_id not in self.data["users"]:
                stats["no_score"] += 1
                continue

            user_data = self.data["users"][user_id]
            member_updated = False

            # Kontrola rolí
            for role_id, role_name, threshold, has_role_key in roles_to_check:
                role = ctx.guild.get_role(role_id)
                if not role:
                    print(f"[AI Mod] Role {role_id} ({role_name}) nebyla nalezena")
                    continue

                # Speciální logika pro negativní roli (práh je horní hranice)
                if role_name == "negative":
                    should_have_role = user_data["total_score"] <= threshold
                else:
                    # Pro pozitivní role je práh dolní hranice
                    should_have_role = user_data["total_score"] >= threshold

                has_role = role in member.roles
                has_role_in_data = user_data.get(has_role_key, False)

                # Synchronizovat stav role
                try:
                    if should_have_role and not has_role:
                        # Přidat roli
                        await member.add_roles(role, reason=f"AI Moderation: Role check - score: {user_data['total_score']}")
                        user_data[has_role_key] = True
                        stats["roles_added"] += 1
                        member_updated = True
                        print(f"[AI Mod] Added {role_name} role to {member.display_name}")
                    elif not should_have_role and has_role:
                        # Odebrat roli
                        await member.remove_roles(role, reason=f"AI Moderation: Role check - score: {user_data['total_score']}")
                        user_data[has_role_key] = False
                        stats["roles_removed"] += 1
                        member_updated = True
                        print(f"[AI Mod] Removed {role_name} role from {member.display_name}")

                    # Synchronizovat stav v datech, pokud se liší od skutečnosti
                    if has_role != has_role_in_data:
                        user_data[has_role_key] = has_role
                        member_updated = True
                except Exception as e:
                    print(f"[AI Mod] Error updating roles for {member.display_name}: {e}")
                    stats["errors"] += 1

            # Uložit změny v datech
            if member_updated:
                stats["members_updated"] += 1
                self.save_data()

            # Aktualizovat zprávu o stavu každých 10 členů
            if i % 10 == 0:
                await status_message.edit(content=f"⏳ Kontroluji role... {i}/{total_members} členů zkontrolováno")

        # Vytvořit embed s výsledky
        embed = discord.Embed(
            title="✅ Kontrola rolí dokončena",
            description="Kontrola a oprava rolí podle AI skóre byla dokončena.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Statistiky",
            value=f"**Zkontrolováno členů:** {stats['checked']}\n"
                  f"**Členů bez skóre:** {stats['no_score']}\n"
                  f"**Přidáno rolí:** {stats['roles_added']}\n"
                  f"**Odebráno rolí:** {stats['roles_removed']}\n"
                  f"**Aktualizováno členů:** {stats['members_updated']}\n"
                  f"**Chyby:** {stats['errors']}",
            inline=False
        )

        embed.set_footer(text="AI moderační systém")
        embed.timestamp = datetime.datetime.now()

        await status_message.edit(content=None, embed=embed)

    @commands.command(name="airules")
    @commands.has_permissions(administrator=True)
    async def ai_rules(self, ctx):
        """Zobrazí pravidla bodovacího systému AI moderace (admin only)"""
        embed = discord.Embed(
            title="Pravidla bodovacího systému AI moderace",
            description="Detailní informace o fungování AI moderace na serveru.",
            color=discord.Color.blue()
        )

        # Batch size
        embed.add_field(
            name="Analýza zpráv",
            value=f"Bot analyzuje **{AI_MESSAGES_BATCH}** zpráv od každého uživatele najednou.\n"
                  f"Analýza probíhá pomocí Google Gemini AI modelu **{AI_MODEL}**.\n"
                  f"Interval kontroly: **{AI_MODERATION_INTERVAL_MINUTES}** minut.",
            inline=False
        )

        # Moderated channels
        if AI_MODERATION_CHANNEL_IDS:
            channel_mentions = []
            for channel_id in AI_MODERATION_CHANNEL_IDS:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    channel_mentions.append(f"<#{channel_id}>")
                else:
                    channel_mentions.append(f"ID: {channel_id}")

            embed.add_field(
                name="Moderované kanály",
                value=f"AI moderace je aktivní pouze v těchto kanálech:\n"
                      f"{', '.join(channel_mentions)}",
                inline=False
            )
        else:
            embed.add_field(
                name="Moderované kanály",
                value=f"AI moderace je aktivní ve všech kanálech.",
                inline=False
            )

        # Scoring system
        embed.add_field(
            name="Bodovací systém",
            value=f"Každá zpráva dostane pozitivní a negativní skóre.\n"
                  f"Velmi negativní zprávy dostanou extra penalizaci **{AI_NEGATIVE_PENALTY}** bodů.\n"
                  f"Celkové skóre = Pozitivní body - Negativní body.\n"
                  f"Systém je nastaven tak, aby byl shovívavý a dával přednost pozitivnímu hodnocení.",
            inline=False
        )

        # Positive thresholds
        embed.add_field(
            name="Pozitivní hranice",
            value=f"🌟 Úroveň 1 (**{AI_POSITIVE_THRESHOLD_1}** bodů): Základní pozitivní role\n"
                  f"🌟🌟 Úroveň 2 (**{AI_POSITIVE_THRESHOLD_2}** bodů): Střední pozitivní role\n"
                  f"🌟🌟🌟 Úroveň 3 (**{AI_POSITIVE_THRESHOLD_3}** bodů): Nejvyšší pozitivní role",
            inline=False
        )

        # Negative thresholds
        embed.add_field(
            name="Negativní hranice",
            value=f"⚠️ Upozornění moderátorům (**{AI_NEGATIVE_THRESHOLD}** bodů): Systém upozorní moderátory\n"
                  f"⛔ Negativní role (**{AI_VERY_NEGATIVE_THRESHOLD}** bodů): Přidělení negativní role",
            inline=False
        )

        # Timeout system
        embed.add_field(
            name="Systém upozornění",
            value=f"**AUTOMATICKÉ TIMEOUTY A UPOZORNĚNÍ JSOU VYPNUTY**\n\n"
                  f"Systém pouze počítá skóre, ale neposílá upozornění při dosažení negativního skóre (**{AI_NEGATIVE_THRESHOLD}** bodů).\n"
                  f"Moderátoři mohou použít příkaz `!timeout @uživatel [čas]` pro ruční udělení timeoutu.",
            inline=False
        )

        # Admin info
        embed.add_field(
            name="Administrátoři",
            value=f"Administrátoři jsou analyzováni, ale nejsou jim udělovány tresty.\n"
                  f"Jejich skóre je vidět v příkazech !aiscore, !aitop a !aibottom.",
            inline=False
        )

        # Commands
        embed.add_field(
            name="Příkazy",
            value=f"!aiscore [@uživatel] - Zobrazí skóre uživatele\n"
                  f"!aitop - Zobrazí top 10 uživatelů\n"
                  f"!aibottom - Zobrazí 10 nejhorších uživatelů\n"
                  f"!aireset [@uživatel] - Resetuje skóre uživatele (admin)\n"
                  f"!airesetall - Resetuje všechna skóre (admin)\n"
                  f"!airules - Zobrazí tato pravidla (admin)\n"
                  f"!aicheck - Zkontroluje a opraví role všech členů (admin)",
            inline=False
        )

        # Footer
        embed.set_footer(text="AI moderační systém")
        embed.timestamp = datetime.datetime.now()

        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

        # Sort users by total score (ascending)
        sorted_users = sorted(
            self.data["users"].items(),
            key=lambda x: x[1]["total_score"]
        )

        # Take bottom 10
        bottom_users = sorted_users[:10]

        # Create embed
        embed = discord.Embed(
            title="⚠️ AI Skóre - Nejhorších 10 uživatelů",
            description="Žebříček uživatelů s nejnižším AI skóre",
            color=discord.Color.red()
        )

        # Add user fields
        for i, (user_id, data) in enumerate(bottom_users, 1):
            username = data["username"] or "Neznámý uživatel"

            embed.add_field(
                name=f"{i}. {username}",
                value=f"Skóre: **{data['total_score']}**\n"
                      f"Pozitivní: **{data['positive_score']}**\n"
                      f"Negativní: **{data['negative_score']}**",
                inline=True
            )

            # Add empty field every 2 entries for better formatting
            if i % 2 == 0 and i < len(bottom_users):
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        # Add footer
        embed.set_footer(text="AI moderační systém")
        embed.timestamp = datetime.datetime.now()

        # Send embed
        await ctx.send(embed=embed, ephemeral=True)

    @commands.command(name="aireset")
    @commands.has_permissions(administrator=True)
    async def reset_ai_score(self, ctx, member: discord.Member):
        """Resetuje AI skóre uživatele (admin only)"""
        user_id = str(member.id)

        if user_id in self.data["users"]:
            # Reset user data
            self.data["users"][user_id] = {
                "username": member.display_name,
                "positive_score": 0,
                "negative_score": 0,
                "total_score": 0,
                "messages_analyzed": 0,
                "last_analyzed": None,
                "timeout_count": 0,
                "last_timeout": None,
                "has_positive_role_1": False,
                "has_positive_role_2": False,
                "has_positive_role_3": False,
                "has_negative_role": False,
                "last_role_update_1": None,
                "last_role_update_2": None,
                "last_role_update_3": None,
                "last_negative_role_update": None
            }
            self.save_data()
            print(f"[AI Mod] Reset AI score for {member.display_name} by admin {ctx.author.display_name}")

            # Remove all roles
            roles_to_check = []
            if AI_POSITIVE_ROLE_ID_1:
                roles_to_check.append((AI_POSITIVE_ROLE_ID_1, "level 1 positive"))
            if AI_POSITIVE_ROLE_ID_2:
                roles_to_check.append((AI_POSITIVE_ROLE_ID_2, "level 2 positive"))
            if AI_POSITIVE_ROLE_ID_3:
                roles_to_check.append((AI_POSITIVE_ROLE_ID_3, "level 3 positive"))
            if AI_NEGATIVE_ROLE_ID:
                roles_to_check.append((AI_NEGATIVE_ROLE_ID, "negative"))

            for role_id, role_name in roles_to_check:
                role = ctx.guild.get_role(role_id)
                if role and role in member.roles:
                    await member.remove_roles(role, reason="AI Moderation: Score reset by admin")
                    print(f"[AI Mod] Removed {role_name} role from {member.display_name}")

            await ctx.send(f"AI skóre uživatele {member.mention} bylo resetováno.", ephemeral=True)
        else:
            await ctx.send(f"Uživatel {member.mention} nemá žádné AI skóre k resetování.", ephemeral=True)

    @commands.command(name="airesetall")
    @commands.has_permissions(administrator=True)
    async def reset_all_ai_scores(self, ctx):
        """Resetuje AI skóre všech uživatelů (admin only)"""
        # Confirm action
        confirm_message = await ctx.send(
            "⚠️ **VAROVÁNÍ**: Tato akce resetuje AI skóre **VŠECH** uživatelů. Pokračovat?",
            ephemeral=True
        )

        # Add reactions for confirmation
        await confirm_message.add_reaction("✅")
        await confirm_message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_message.id

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction.emoji) == "✅":
                # Reset all user data
                self.data["users"] = {}
                self.save_data()
                print(f"[AI Mod] All user scores reset by admin {ctx.author.display_name}")

                # Remove all roles from all members
                roles_to_check = []
                if AI_POSITIVE_ROLE_ID_1:
                    roles_to_check.append((AI_POSITIVE_ROLE_ID_1, "level 1 positive"))
                if AI_POSITIVE_ROLE_ID_2:
                    roles_to_check.append((AI_POSITIVE_ROLE_ID_2, "level 2 positive"))
                if AI_POSITIVE_ROLE_ID_3:
                    roles_to_check.append((AI_POSITIVE_ROLE_ID_3, "level 3 positive"))
                if AI_NEGATIVE_ROLE_ID:
                    roles_to_check.append((AI_NEGATIVE_ROLE_ID, "negative"))

                for role_id, role_name in roles_to_check:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        for member in role.members:
                            await member.remove_roles(role, reason="AI Moderation: All scores reset by admin")
                            print(f"[AI Mod] Removed {role_name} role from {member.display_name}")

                await ctx.send("AI skóre všech uživatelů bylo resetováno.", ephemeral=True)
            else:
                await ctx.send("Akce zrušena.", ephemeral=True)

        except asyncio.TimeoutError:
            await ctx.send("Čas na potvrzení vypršel. Akce zrušena.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIModeration(bot))
