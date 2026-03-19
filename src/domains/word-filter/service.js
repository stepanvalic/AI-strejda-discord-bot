import { escapeRegExp } from '../../shared/utils.js';
import { createEmbed, isAdminMember } from '../../shared/discord-helpers.js';

export class WordFilterService {
  constructor(context) {
    this.context = context;
  }

  async handleMessage(message) {
    if (!message.guild || message.author.bot || isAdminMember(message.member)) {
      return false;
    }

    const blacklist = await this.context.database.blacklist.read();
    const words = blacklist.blacklisted_words.map((word) => word.toLowerCase());
    if (!words.length) {
      return false;
    }

    const lowered = message.content.toLowerCase();
    const foundWords = words.filter((word) => new RegExp(`\\b${escapeRegExp(word)}\\b`, 'u').test(lowered));

    if (!foundWords.length) {
      return false;
    }

    await message.delete().catch(() => null);
    await this.context.database.filteredWords.update((store) => {
      store.filtered_messages.push({
        user_id: message.author.id,
        username: message.author.username,
        channel_id: message.channelId,
        channel_name: message.channel.name,
        content: message.content,
        found_words: foundWords,
        timestamp: new Date().toISOString()
      });
      return store;
    });

    await this.context.services.audit.send(message.guild, createEmbed({
      title: 'Word filter trefil zprávu',
      description: `Smazáno od ${message.author.tag}`,
      fields: [
        { name: 'Slova', value: foundWords.join(', ') },
        { name: 'Kanál', value: `<#${message.channelId}>` }
      ]
    }));

    return true;
  }

  async addWord(word, channelId) {
    const config = await this.context.configStore.get();

    if (channelId !== config.audit.channelId) {
      return { added: false, reason: 'Tahle akce je povolena jen v audit kanálu.' };
    }

    const normalized = word.trim().toLowerCase();

    if (!normalized) {
      throw new Error('Slovo nesmí být prázdné.');
    }

    await this.context.database.blacklist.update((store) => {
      if (!store.blacklisted_words.includes(normalized)) {
        store.blacklisted_words.push(normalized);
      }

      return store;
    });

    return { added: true, word: normalized };
  }
}
