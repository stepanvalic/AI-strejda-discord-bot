import { Colors } from 'discord.js';
import { createEmbed } from '../../shared/discord-helpers.js';
import { parseCountingExpression } from './expression.js';

function ensureUserStats(state, user) {
  if (!state.user_stats[user.id]) {
    state.user_stats[user.id] = {
      username: user.username,
      correct_counts: 0,
      wrong_counts: 0,
      last_updated: null,
      consecutive_fails: 0,
      total_blocks: 0
    };
  }

  if (state.user_stats[user.id].total_blocks === undefined) {
    state.user_stats[user.id].total_blocks = 0;
  }

  if (state.user_stats[user.id].consecutive_fails === undefined) {
    state.user_stats[user.id].consecutive_fails = 0;
  }

  return state.user_stats[user.id];
}

function calculateBlockDurationDays(stats) {
  return stats.total_blocks > 0 ? 3 : 1;
}

export class CountingService {
  constructor(context) {
    this.context = context;
  }

  async handleMessage(message) {
    const config = await this.context.configStore.get();

    if (!config.features.counting || message.author.bot || message.channelId !== config.counting.channelId) {
      return false;
    }

    const state = await this.context.database.counting.read();
    const blocked = state.blocked_users[message.author.id];

    if (blocked && new Date(blocked.end_time) > new Date()) {
      await message.delete().catch(() => null);
      await message.author.send(`V countingu jsi blokovaný do ${blocked.end_time}.`).catch(() => null);
      return true;
    }

    if (blocked && new Date(blocked.end_time) <= new Date()) {
      await this.context.database.counting.update((store) => {
        delete store.blocked_users[message.author.id];
        return store;
      });
    }

    let value;

    try {
      value = parseCountingExpression(message.content);
    } catch {
      await message.delete().catch(() => null);
      return true;
    }

    const expected = state.current_count + 1;
    const sameUserTwice = String(state.last_user_id) === message.author.id;
    const nextState = structuredClone(state);
    const userStats = ensureUserStats(nextState, message.author);
    userStats.username = message.author.username;
    userStats.last_updated = new Date().toISOString();

    if (sameUserTwice || value !== expected) {
      nextState.current_count = 0;
      nextState.last_user_id = null;
      nextState.failed_counts += 1;
      userStats.wrong_counts += 1;
      userStats.consecutive_fails += 1;

      const shouldBlock =
        (userStats.total_blocks === 0 && userStats.consecutive_fails >= 5) ||
        (userStats.total_blocks > 0 && userStats.consecutive_fails >= 2);

      if (shouldBlock) {
        const durationDays = calculateBlockDurationDays(userStats);
        const blockedAt = new Date();
        const endTime = new Date(blockedAt.getTime() + durationDays * 86_400_000);
        nextState.blocked_users[message.author.id] = {
          username: message.author.username,
          blocked_at: blockedAt.toISOString(),
          end_time: endTime.toISOString(),
          duration_days: durationDays,
          last_notification: blockedAt.toISOString()
        };
        userStats.total_blocks += 1;
        userStats.consecutive_fails = 0;
      }

      await this.context.database.counting.write(nextState);
      await message.react('❌').catch(() => null);
      await message.channel.send({
        embeds: [
          createEmbed({
            title: 'Counting reset',
            color: Colors.Red,
            description: sameUserTwice
              ? `${message.author} poslal dvě správná čísla po sobě. Počítání jde zpátky na nulu.`
              : `${message.author} poslal \`${value}\`, ale čekalo se \`${expected}\`. Reset.`
          })
        ]
      });
      return true;
    }

    nextState.current_count = value;
    nextState.last_user_id = message.author.id;
    nextState.high_score = Math.max(nextState.high_score, value);
    userStats.correct_counts += 1;
    userStats.consecutive_fails = 0;

    await this.context.database.counting.write(nextState);
    this.context.runtime.countingLastValidMessage = {
      messageId: message.id,
      channelId: message.channelId,
      content: message.content,
      userId: message.author.id
    };

    await message.react('✅').catch(() => null);
    return true;
  }

  async restoreLastValidMessage(messageLike) {
    const cached = this.context.runtime.countingLastValidMessage;
    if (!cached || cached.messageId !== messageLike.id) {
      return;
    }

    if (messageLike.channel?.isTextBased?.()) {
      await messageLike.channel.send(`Obnovuju poslední validní číslo: \`${cached.content}\``);
    }
  }

  async getStatus() {
    const state = await this.context.database.counting.read();
    return {
      current: state.current_count,
      expected: state.current_count + 1,
      highScore: state.high_score,
      failedCounts: state.failed_counts
    };
  }

  async reset() {
    return this.context.database.counting.update((store) => {
      store.current_count = 0;
      store.last_user_id = null;
      return store;
    });
  }

  async blockUser(member, days) {
    if (member.permissions.has('Administrator')) {
      throw new Error('Admin nejde blokovat.');
    }

    const durationDays = Math.max(1, days);
    const blockedAt = new Date();
    const endTime = new Date(blockedAt.getTime() + durationDays * 86_400_000);

    return this.context.database.counting.update((store) => {
      const stats = ensureUserStats(store, member.user);
      stats.total_blocks += 1;
      stats.consecutive_fails = 0;
      store.blocked_users[member.id] = {
        username: member.user.username,
        blocked_at: blockedAt.toISOString(),
        end_time: endTime.toISOString(),
        duration_days: durationDays,
        last_notification: blockedAt.toISOString()
      };
      return store;
    });
  }

  async listBlocked() {
    const state = await this.context.database.counting.read();
    return Object.entries(state.blocked_users).map(([userId, entry]) => ({
      userId,
      ...entry
    }));
  }

  async unblockUser(userId) {
    return this.context.database.counting.update((store) => {
      delete store.blocked_users[userId];
      if (store.user_stats[userId]) {
        store.user_stats[userId].consecutive_fails = 0;
      }
      return store;
    });
  }

  async setChannel(channelId) {
    return this.context.configStore.update((current) => {
      current.counting.channelId = channelId;
      return current;
    });
  }

  async getStats(userId) {
    const state = await this.context.database.counting.read();

    if (userId) {
      return state.user_stats[userId] ?? null;
    }

    return Object.entries(state.user_stats)
      .map(([id, stats]) => ({ userId: id, ...stats }))
      .sort((left, right) => right.correct_counts - left.correct_counts)
      .slice(0, 10);
  }

  getRulesText() {
    return [
      'Pocita se po jedne nahoru.',
      'Stejný člověk nesmí poslat dvě správná čísla po sobě.',
      'Podporena jsou celá čísla, hex, bin, oct a bezpečné výrazy.',
      'Chyba resetuje count na nulu.',
      'Po sérii failů můžeš dostat blok.'
    ].join('\n');
  }

  getFormatsText() {
    return [
      '`255`',
      '`0xFF`',
      '`0b11111111`',
      '`0o377`',
      '`(2 + 3) * 5`'
    ].join('\n');
  }
}
