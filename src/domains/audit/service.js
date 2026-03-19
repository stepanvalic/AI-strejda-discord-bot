import { Colors } from 'discord.js';
import { createEmbed, fetchTextChannel } from '../../shared/discord-helpers.js';
import { mentionChannel, mentionRole, mentionUser, truncate } from '../../shared/utils.js';

export class AuditService {
  constructor(context) {
    this.context = context;
  }

  async getChannel(guild) {
    const config = await this.context.configStore.get();
    return fetchTextChannel(guild, config.audit.channelId);
  }

  async send(guild, embed) {
    const channel = await this.getChannel(guild);
    if (!channel) {
      return null;
    }

    return channel.send({ embeds: [embed] });
  }

  async logModerationEvent(payload) {
    const guild = this.context.client.guilds.cache.first();
    if (!guild) {
      return;
    }

    const embed = createEmbed({
      title: `Moderace: ${payload.type}`,
      color: Colors.DarkOrange,
      fields: [
        { name: 'Target', value: mentionUser(payload.targetId), inline: true },
        { name: 'Moderator', value: mentionUser(payload.moderatorId), inline: true },
        { name: 'Důvod', value: payload.reason || 'neuveden' }
      ]
    });

    if (payload.durationMs) {
      embed.addFields({ name: 'Délka', value: `${Math.round(payload.durationMs / 60000)} minut`, inline: true });
    }

    await this.send(guild, embed);
  }

  async logMessageDelete(message) {
    await this.send(message.guild, createEmbed({
      title: 'Smazaná zpráva',
      color: Colors.Red,
      fields: [
        { name: 'Autor', value: mentionUser(message.author?.id), inline: true },
        { name: 'Kanál', value: mentionChannel(message.channelId), inline: true },
        { name: 'Obsah', value: truncate(message.content || '(prázdné)') }
      ]
    }));
  }

  async logMessageUpdate(oldMessage, newMessage) {
    if (!oldMessage.content || oldMessage.content === newMessage.content) {
      return;
    }

    await this.send(newMessage.guild, createEmbed({
      title: 'Editace zprávy',
      color: Colors.Yellow,
      fields: [
        { name: 'Autor', value: mentionUser(newMessage.author?.id), inline: true },
        { name: 'Kanál', value: mentionChannel(newMessage.channelId), inline: true },
        { name: 'Před', value: truncate(oldMessage.content) },
        { name: 'Po', value: truncate(newMessage.content) }
      ]
    }));
  }

  async logMemberUpdate(oldMember, newMember) {
    const changes = [];

    if (oldMember.nickname !== newMember.nickname) {
      changes.push({
        name: 'Přezdívka',
        value: `${oldMember.nickname || oldMember.user.username} -> ${newMember.nickname || newMember.user.username}`
      });
    }

    const addedRoles = newMember.roles.cache.filter((role) => !oldMember.roles.cache.has(role.id) && role.id !== newMember.guild.id);
    const removedRoles = oldMember.roles.cache.filter((role) => !newMember.roles.cache.has(role.id) && role.id !== oldMember.guild.id);

    if (addedRoles.size) {
      changes.push({ name: 'Přidané role', value: addedRoles.map((role) => mentionRole(role.id)).join(', ') });
    }

    if (removedRoles.size) {
      changes.push({ name: 'Odebrané role', value: removedRoles.map((role) => mentionRole(role.id)).join(', ') });
    }

    if (!changes.length) {
      return;
    }

    await this.send(newMember.guild, createEmbed({
      title: 'Změna člena',
      color: Colors.Blue,
      fields: [{ name: 'Clen', value: mentionUser(newMember.id) }, ...changes]
    }));
  }

  async logBan(guild, user) {
    await this.send(guild, createEmbed({
      title: 'Guild ban add',
      color: Colors.Red,
      description: `${user.tag} dostal ban.`
    }));
  }

  async logUnban(guild, user) {
    await this.send(guild, createEmbed({
      title: 'Guild ban remove',
      color: Colors.Green,
      description: `${user.tag} byl odbanován.`
    }));
  }

  async logChannelCreate(channel) {
    await this.send(channel.guild, createEmbed({
      title: 'Kanál vytvořen',
      fields: [
        { name: 'Kanál', value: mentionChannel(channel.id), inline: true },
        { name: 'Typ', value: String(channel.type), inline: true }
      ]
    }));
  }

  async logChannelDelete(channel) {
    await this.send(channel.guild, createEmbed({
      title: 'Kanál smazán',
      color: Colors.Red,
      description: `\`${channel.name}\``
    }));
  }

  async logChannelUpdate(oldChannel, newChannel) {
    if (oldChannel.name === newChannel.name) {
      return;
    }

    await this.send(newChannel.guild, createEmbed({
      title: 'Kanál upraven',
      fields: [
        { name: 'Před', value: oldChannel.name, inline: true },
        { name: 'Po', value: newChannel.name, inline: true }
      ]
    }));
  }

  async logRoleCreate(role) {
    await this.send(role.guild, createEmbed({
      title: 'Role vytvořena',
      description: mentionRole(role.id)
    }));
  }

  async logRoleDelete(role) {
    await this.send(role.guild, createEmbed({
      title: 'Role smazána',
      color: Colors.Red,
      description: role.name
    }));
  }

  async logRoleUpdate(oldRole, newRole) {
    if (oldRole.name === newRole.name) {
      return;
    }

    await this.send(newRole.guild, createEmbed({
      title: 'Role upravena',
      fields: [
        { name: 'Před', value: oldRole.name, inline: true },
        { name: 'Po', value: newRole.name, inline: true }
      ]
    }));
  }
}
