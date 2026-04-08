import { formatDateInTimeZone, truncate } from '../../shared/utils.js';

const MAX_OUTPUT_MESSAGES = 20;

function normalizeText(value, fallback = '(bez textu)') {
  if (!value) {
    return fallback;
  }

  const normalized = value.replace(/\s+/gu, ' ').trim();
  return normalized || fallback;
}

function buildAttachmentList(message) {
  return [...message.attachments.values()].map((attachment) => ({
    id: attachment.id,
    name: attachment.name,
    url: attachment.url,
    content_type: attachment.contentType,
    size: attachment.size
  }));
}

function buildEmbedList(message) {
  return message.embeds.map((embed) => ({
    title: embed.title || '',
    description: embed.description || '',
    url: embed.url || '',
    type: embed.type || ''
  }));
}

export class ModerationService {
  constructor(context) {
    this.context = context;
  }

  buildArchivedMessage(message) {
    return {
      message_id: message.id,
      guild_id: message.guild?.id || null,
      channel_id: message.channelId || null,
      channel_name: message.channel?.name || null,
      author_id: message.author?.id || null,
      author_tag: message.author?.tag || null,
      username: message.author?.username || null,
      display_name: message.member?.displayName || message.author?.globalName || message.author?.username || null,
      content: message.content || '',
      created_at: message.createdAt?.toISOString?.() || new Date().toISOString(),
      edited_at: message.editedAt?.toISOString?.() || null,
      deleted_at: null,
      jump_url: message.url || null,
      is_bot: Boolean(message.author?.bot),
      attachments: buildAttachmentList(message),
      embeds: buildEmbedList(message)
    };
  }

  async archiveMessage(message) {
    if (!message.guild || message.guild.id !== this.context.guildId) {
      return false;
    }

    const archivedMessage = this.buildArchivedMessage(message);

    await this.context.database.moderationArchive.update((store) => {
      const existingIndex = store.messages.findIndex((entry) => entry.message_id === message.id);

      if (existingIndex >= 0) {
        store.messages[existingIndex] = {
          ...store.messages[existingIndex],
          ...archivedMessage
        };
        return store;
      }

      store.messages.push(archivedMessage);
      return store;
    });

    return true;
  }

  async updateArchivedMessage(newMessage) {
    if (!newMessage.guild || newMessage.guild.id !== this.context.guildId) {
      return false;
    }

    const nextContent = newMessage.content || '';
    const nextEditedAt = newMessage.editedAt?.toISOString?.() || new Date().toISOString();

    await this.context.database.moderationArchive.update((store) => {
      const existing = store.messages.find((entry) => entry.message_id === newMessage.id);

      if (existing) {
        existing.content = nextContent;
        existing.edited_at = nextEditedAt;
        existing.channel_name = newMessage.channel?.name || existing.channel_name;
        existing.display_name = newMessage.member?.displayName || existing.display_name;
        existing.attachments = buildAttachmentList(newMessage);
        existing.embeds = buildEmbedList(newMessage);
        existing.jump_url = newMessage.url || existing.jump_url;
        return store;
      }

      store.messages.push({
        message_id: newMessage.id,
        guild_id: newMessage.guild.id,
        channel_id: newMessage.channelId || null,
        channel_name: newMessage.channel?.name || null,
        author_id: newMessage.author?.id || null,
        author_tag: newMessage.author?.tag || null,
        username: newMessage.author?.username || null,
        display_name: newMessage.member?.displayName || newMessage.author?.globalName || newMessage.author?.username || null,
        content: nextContent,
        created_at: newMessage.createdAt?.toISOString?.() || new Date().toISOString(),
        edited_at: nextEditedAt,
        deleted_at: null,
        jump_url: newMessage.url || null,
        is_bot: Boolean(newMessage.author?.bot),
        attachments: buildAttachmentList(newMessage),
        embeds: buildEmbedList(newMessage)
      });
      return store;
    });

    return true;
  }

  async markMessageDeleted(message) {
    if (!message.guild || message.guild.id !== this.context.guildId) {
      return false;
    }

    const deletedAt = new Date().toISOString();

    await this.context.database.moderationArchive.update((store) => {
      const existing = store.messages.find((entry) => entry.message_id === message.id);

      if (existing) {
        existing.deleted_at = deletedAt;
        if (message.content && !existing.content) {
          existing.content = message.content;
        }
        return store;
      }

      store.messages.push({
        message_id: message.id,
        guild_id: message.guild.id,
        channel_id: message.channelId || null,
        channel_name: message.channel?.name || null,
        author_id: message.author?.id || null,
        author_tag: message.author?.tag || null,
        username: message.author?.username || null,
        display_name: message.author?.globalName || message.author?.username || null,
        content: message.content || '',
        created_at: message.createdAt?.toISOString?.() || deletedAt,
        edited_at: message.editedAt?.toISOString?.() || null,
        deleted_at: deletedAt,
        jump_url: message.url || null,
        is_bot: Boolean(message.author?.bot),
        attachments: [],
        embeds: []
      });
      return store;
    });

    return true;
  }

  async getArchiveStats() {
    const store = await this.context.database.moderationArchive.read();
    const today = formatDateInTimeZone(new Date(), this.context.env.TIMEZONE);
    const uniqueUsers = new Set();
    const uniqueChannels = new Set();
    let archivedToday = 0;
    let latestMessage = null;

    for (const message of store.messages) {
      if (message.author_id) {
        uniqueUsers.add(message.author_id);
      }

      if (message.channel_id) {
        uniqueChannels.add(message.channel_id);
      }

      if (message.created_at?.slice(0, 10) === today) {
        archivedToday += 1;
      }

      if (!latestMessage || (message.created_at && message.created_at > latestMessage.created_at)) {
        latestMessage = message;
      }
    }

    return {
      totalMessages: store.messages.length,
      archivedToday,
      uniqueUsers: uniqueUsers.size,
      uniqueChannels: uniqueChannels.size,
      latestMessage
    };
  }

  async findMessages({ limit = 10, query = '', channelId = null, userId = null } = {}) {
    const store = await this.context.database.moderationArchive.read();
    const normalizedQuery = query.trim().toLowerCase();
    const safeLimit = Math.max(1, Math.min(limit, MAX_OUTPUT_MESSAGES));

    const messages = store.messages
      .filter((message) => {
        if (channelId && message.channel_id !== channelId) {
          return false;
        }

        if (userId && message.author_id !== userId) {
          return false;
        }

        if (normalizedQuery) {
          const haystack = `${message.content || ''} ${message.display_name || ''} ${message.username || ''}`.toLowerCase();
          return haystack.includes(normalizedQuery);
        }

        return true;
      })
      .sort((left, right) => (right.created_at || '').localeCompare(left.created_at || ''))
      .slice(0, safeLimit);

    return messages;
  }

  formatMessageLine(message) {
    const parts = [
      `[${message.created_at?.slice(0, 19)?.replace('T', ' ') || 'bez času'}]`,
      `#${message.channel_name || 'neznámý-kanál'}`,
      `${message.display_name || message.username || message.author_id || 'neznámý autor'}:`,
      normalizeText(truncate(message.content, 160))
    ];

    if (message.deleted_at) {
      parts.push('(smazaná)');
    } else if (message.edited_at) {
      parts.push('(editovaná)');
    }

    if (!message.content && message.attachments?.length) {
      parts.push(`(${message.attachments.length} příloha/přílohy)`);
    }

    return parts.join(' ');
  }

  formatMessageList(messages) {
    if (!messages.length) {
      return 'V archivu jsem nic nenašel.';
    }

    return messages.map((message) => this.formatMessageLine(message)).join('\n');
  }
}
