import discord
from discord.ext import commands
from utils import config

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_messages = {}
        self.channel_id = config.get_int('REACTION_ROLES_CHANNEL_ID')
        self.message_id = config.get_int('REACTION_ROLES_MESSAGE_ID')
        self.role_emojis = self.parse_role_emojis(config.get('REACTION_ROLES_MAPPINGS'))

    def parse_role_emojis(self, mappings_str):
        """Parse role_id:emoji mappings from config string"""
        mappings = {}
        if not mappings_str:
            return mappings
            
        for pair in mappings_str.split(','):
            role_id, emoji = pair.split(':', 1)
            mappings[int(role_id.strip())] = emoji.strip()
        return mappings

    async def setup_message(self):
        """Create or update the reaction roles message"""
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print("Reaction roles channel not found!")
            return
            
        if self.message_id:
            try:
                message = await channel.fetch_message(self.message_id)
                await message.clear_reactions()
            except discord.NotFound:
                message = None
        else:
            message = None
            
        if not message:
            embed = discord.Embed(
                title="Reakce pro získání rolí",
                description="Klikni na reakci níže pro získání role",
                color=discord.Color.blue()
            )
            message = await channel.send(embed=embed)
            config.set('REACTION_ROLES_MESSAGE_ID', str(message.id))
            
        # Add reactions
        for emoji in self.role_emojis.values():
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.setup_message()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.message_id:
            return
            
        if payload.user_id == self.bot.user.id:
            return
            
        emoji = str(payload.emoji)
        role_id = next((rid for rid, e in self.role_emojis.items() if e == emoji), None)
        if not role_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id)
        
        if member and role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                print(f"Missing permissions to add role {role.name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id != self.message_id:
            return
            
        emoji = str(payload.emoji)
        role_id = next((rid for rid, e in self.role_emojis.items() if e == emoji), None)
        if not role_id:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id)
        
        if member and role:
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                print(f"Missing permissions to remove role {role.name}")

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))