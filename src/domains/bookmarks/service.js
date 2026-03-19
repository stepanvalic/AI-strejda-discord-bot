import { parseMessageLink } from '../../shared/discord-helpers.js';
import { chunkArray } from '../../shared/utils.js';

export class BookmarkService {
  constructor(context) {
    this.context = context;
  }

  async saveFromLink(ownerId, link, note, guild) {
    const parsed = parseMessageLink(link);

    if (!parsed) {
      throw new Error('Tohle nevypada jako Discord message link.');
    }

    const channel = guild.channels.cache.get(parsed.channelId) ?? await guild.channels.fetch(parsed.channelId);
    const message = await channel.messages.fetch(parsed.messageId);

    await this.context.database.bookmarks.update((store) => {
      const bookmarks = store[ownerId] ?? [];
      bookmarks.push({
        content: message.content,
        author: message.author.username,
        author_id: message.author.id,
        channel_name: channel.name,
        channel_id: channel.id,
        message_id: message.id,
        timestamp: message.createdAt.toISOString(),
        jump_url: message.url,
        note: note || null,
        saved_at: new Date().toISOString(),
        attachments: [...message.attachments.values()].map((attachment) => attachment.url)
      });
      store[ownerId] = bookmarks;
      return store;
    });
  }

  async list(ownerId, page = 1) {
    const store = await this.context.database.bookmarks.read();
    const bookmarks = store[ownerId] ?? [];
    const pages = chunkArray(bookmarks, 5);
    const resolvedPage = Math.max(1, Math.min(page, Math.max(pages.length, 1)));
    return {
      page: resolvedPage,
      totalPages: Math.max(pages.length, 1),
      items: pages[resolvedPage - 1] ?? []
    };
  }

  async delete(ownerId, index) {
    const zeroIndex = index - 1;

    return this.context.database.bookmarks.update((store) => {
      const bookmarks = store[ownerId] ?? [];
      if (zeroIndex < 0 || zeroIndex >= bookmarks.length) {
        throw new Error('Bookmark s timhle cislem neexistuje.');
      }

      bookmarks.splice(zeroIndex, 1);
      store[ownerId] = bookmarks;
      return store;
    });
  }
}
