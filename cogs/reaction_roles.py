import discord
from discord.ext import commands
from utils import config

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = config.get_int('REACTION_ROLES_CHANNEL_ID')
        self.message_id = config.get_int('REACTION_ROLES_MESSAGE_ID')
        self.role_mappings = self.parse_role_mappings(config.get('REACTION_ROLES_MAPPINGS'))

    def parse_role_mappings(self, mappings):
        """Parse role mappings from config"""
        role_data = []
        for mapping in mappings:
            parts = mapping.split('=')
            if len(parts) == 3:  # role_id=emoji=description
                role_id, emoji, description = parts
                role_data.append({
                    'role_id': int(role_id.strip()),
                    'emoji': emoji.strip(),
                    'description': description.strip()
                })
        return role_data

    async def create_role_embed(self, guild):
        """Create embed with role descriptions"""
        embed = discord.Embed(
            title="📌 Reakce pro získání rolí",
            description="Klikni na reakci pod zprávou pro získání role",
            color=discord.Color.blue()
        )
        
        for mapping in self.role_mappings:
            role = guild.get_role(mapping['role_id'])
            if role:
                embed.add_field(
                    name=f"{mapping['emoji']} {role.name}",
                    value=mapping['description'],
                    inline=False
                )
        
        embed.set_footer(text="Reakci můžeš kdykoliv odebrat a role se ti odstraní")
        return embed

    async def setup_message(self):
        """Create or update the reaction roles message"""
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print("Reaction roles channel not found!")
            return
            
        try:
            # Try to fetch existing message
            message = await channel.fetch_message(self.message_id) if self.message_id else None
        except discord.NotFound:
            message = None
            
        # Create new embed
        guild = channel.guild
        embed = await self.create_role_embed(guild)
        
        if message:
            # Edit existing message
            await message.edit(embed=embed)
            await message.clear_reactions()
        else:
            # Create new message
            message = await channel.send(embed=embed)
            config.set('REACTION_ROLES_MESSAGE_ID', str(message.id))
            
        # Add reactions
        for mapping in self.role_mappings:
            await message.add_reaction(mapping['emoji'])

    @commands.Cog.listener()
    async def on_ready(self):
        await self.setup_message()

    async def handle_reaction(self, payload, add_role):
        """Handle reaction add/remove"""
        if payload.message_id != self.message_id:
            return
            
        if payload.user_id == self.bot.user.id:
            return
            
        emoji = str(payload.emoji)
        mapping = next((m for m in self.role_mappings if m['emoji'] == emoji), None)
        if not mapping:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(mapping['role_id'])
        
        if member and role:
            try:
                if add_role:
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)
            except discord.Forbidden:
                print(f"Missing permissions to modify role {role.name}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.handle_reaction(payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.handle_reaction(payload, False)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))