import { Colors } from 'discord.js';
import { createEmbed, fetchTextChannel, normalizeEmoji } from '../../shared/discord-helpers.js';

export class ReactionRoleService {
  constructor(context) {
    this.context = context;
  }

  async syncMessage(guild) {
    const config = await this.context.configStore.get();
    const channel = await fetchTextChannel(guild, config.reactionRoles.channelId);

    if (!channel) {
      throw new Error('Reaction role kanál není nastavený.');
    }

    const embed = createEmbed({
      title: 'Reaction role panel',
      color: Colors.Gold,
      description: config.reactionRoles.mappings.length
        ? config.reactionRoles.mappings.map((mapping) => `${mapping.emoji} <@&${mapping.roleId}> - ${mapping.description}`).join('\n')
        : 'Zatím tu nic není.'
    });

    let message = null;

    if (config.reactionRoles.messageId) {
      message = await channel.messages.fetch(config.reactionRoles.messageId).catch(() => null);
    }

    if (message) {
      await message.edit({ embeds: [embed] });
    } else {
      message = await channel.send({ embeds: [embed] });
      await this.context.configStore.update((current) => {
        current.reactionRoles.messageId = message.id;
        return current;
      });
    }

    for (const mapping of config.reactionRoles.mappings) {
      const hasReaction = message.reactions.cache.some((reaction) => normalizeEmoji(reaction.emoji) === normalizeEmoji(mapping.emoji));
      if (!hasReaction) {
        await message.react(mapping.emoji).catch(() => null);
      }
    }

    return message;
  }

  async handleReactionChange(reaction, user, addRole) {
    if (user.bot) {
      return;
    }

    if (reaction.partial) {
      await reaction.fetch().catch(() => null);
    }

    const config = await this.context.configStore.get();

    if (reaction.message.id !== config.reactionRoles.messageId) {
      return;
    }

    const mapping = config.reactionRoles.mappings.find(
      (entry) => normalizeEmoji(entry.emoji) === normalizeEmoji(reaction.emoji)
    );

    if (!mapping) {
      return;
    }

    const member = await reaction.message.guild.members.fetch(user.id).catch(() => null);
    if (!member) {
      return;
    }

    if (addRole) {
      await member.roles.add(mapping.roleId, 'Reaction role add');
    } else {
      await member.roles.remove(mapping.roleId, 'Reaction role remove');
    }
  }
}
