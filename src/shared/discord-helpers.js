import { Colors, EmbedBuilder, PermissionFlagsBits } from 'discord.js';
import { truncate } from './utils.js';

export function isAdminMember(member) {
  return Boolean(member?.permissions?.has?.(PermissionFlagsBits.Administrator));
}

export function createEmbed({ title, description, color = Colors.Blurple, fields = [], footer, timestamp = true }) {
  const embed = new EmbedBuilder().setColor(color);

  if (title) {
    embed.setTitle(title);
  }

  if (description) {
    embed.setDescription(truncate(description, 4000));
  }

  if (fields.length) {
    embed.addFields(fields.map((field) => ({
      ...field,
      value: truncate(field.value, 1024)
    })));
  }

  if (footer) {
    embed.setFooter({ text: footer });
  }

  if (timestamp) {
    embed.setTimestamp(new Date());
  }

  return embed;
}

export async function fetchTextChannel(guild, channelId) {
  if (!guild || !channelId) {
    return null;
  }

  const channel = guild.channels.cache.get(channelId) ?? await guild.channels.fetch(channelId).catch(() => null);

  if (!channel?.isTextBased?.()) {
    return null;
  }

  return channel;
}

export function normalizeEmoji(input) {
  if (!input) {
    return '';
  }

  if (typeof input === 'string') {
    return input.trim();
  }

  if (input.id && input.name) {
    return `<:${input.name}:${input.id}>`;
  }

  if (input.name) {
    return input.name;
  }

  return String(input);
}

export function parseMessageLink(link) {
  const match = link.match(/discord\.com\/channels\/(\d+)\/(\d+)\/(\d+)/u);

  if (!match) {
    return null;
  }

  return {
    guildId: match[1],
    channelId: match[2],
    messageId: match[3]
  };
}
