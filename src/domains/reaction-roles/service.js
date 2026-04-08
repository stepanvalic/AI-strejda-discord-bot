import { Colors } from 'discord.js';
import { createEmbed, fetchTextChannel, normalizeEmoji } from '../../shared/discord-helpers.js';

export class ReactionRoleService {
  constructor(context) {
    this.context = context;
    this.recentAdds = new Map();
  }

  createRecentAddKey(messageId, userId, emoji) {
    return `${messageId}:${userId}:${normalizeEmoji(emoji)}`;
  }

  async setChannelAndSyncMessage(guild, channelId) {
    await this.context.configStore.update((current) => {
      current.reactionRoles.channelId = channelId;
      current.reactionRoles.messageId = '';
      return current;
    });

    return this.syncMessage(guild);
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

    const recentAddKey = this.createRecentAddKey(reaction.message.id, user.id, reaction.emoji);

    if (addRole) {
      this.recentAdds.set(recentAddKey, Date.now());

      if (!member.roles.cache.has(mapping.roleId)) {
        await member.roles.add(mapping.roleId, 'Reaction role add');
      }

      return;
    }

    const recentAddAt = this.recentAdds.get(recentAddKey);
    if (recentAddAt && (Date.now() - recentAddAt) < 5000) {
      return;
    }

    this.recentAdds.delete(recentAddKey);

    if (member.roles.cache.has(mapping.roleId)) {
      await member.roles.remove(mapping.roleId, 'Reaction role remove');
    }
  }
}
