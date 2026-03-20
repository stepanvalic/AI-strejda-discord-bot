import { Colors } from 'discord.js';
import { createEmbed } from '../../shared/discord-helpers.js';
import { mentionChannel, toDiscordTimestamp } from '../../shared/utils.js';
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

function formatCzechDays(days) {
  if (days === 1) {
    return '1 den';
  }

  if (days >= 2 && days <= 4) {
    return `${days} dny`;
  }

  return `${days} dní`;
}

function formatRemainingTime(dateLike) {
  const target = new Date(dateLike);
  const diff = target.getTime() - Date.now();

  if (diff <= 0) {
    return 'už vypršelo';
  }

  const totalMinutes = Math.floor(diff / 60000);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;
  const parts = [];

  if (days) {
    parts.push(formatCzechDays(days));
  }

  if (hours) {
    parts.push(hours === 1 ? '1 hodina' : (hours >= 2 && hours <= 4 ? `${hours} hodiny` : `${hours} hodin`));
  }

  if (minutes && !days) {
    parts.push(minutes === 1 ? '1 minuta' : (minutes >= 2 && minutes <= 4 ? `${minutes} minuty` : `${minutes} minut`));
  }

  return parts.join(' ');
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

  async getStatusEmbed() {
    const config = await this.context.configStore.get();
    const status = await this.getStatus();

    return createEmbed({
      title: '🔢 Počítání',
      description: `Aktuální stav countingu v ${mentionChannel(config.counting.channelId)}.`,
      color: Colors.Blue,
      fields: [
        { name: 'Aktuální číslo', value: String(status.current), inline: true },
        { name: 'Další číslo', value: String(status.expected), inline: true },
        { name: 'Rekord', value: String(status.highScore), inline: true },
        { name: 'Počet selhání', value: String(status.failedCounts), inline: true }
      ]
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

  async getBlockedEmbed() {
    const config = await this.context.configStore.get();
    const blocked = (await this.listBlocked())
      .filter((entry) => new Date(entry.end_time) > new Date())
      .sort((left, right) => new Date(left.end_time) - new Date(right.end_time));

    if (!blocked.length) {
      return createEmbed({
        title: '⛔ Blokovaní uživatelé',
        description: `V ${mentionChannel(config.counting.channelId)} aktuálně není nikdo blokovaný.`,
        color: Colors.Green
      });
    }

    return createEmbed({
      title: '⛔ Blokovaní uživatelé',
      description: `Aktivní blokace pro ${mentionChannel(config.counting.channelId)}.`,
      color: Colors.Red,
      fields: blocked.map((entry) => ({
        name: `${entry.username} (${entry.userId})`,
        value: [
          `Blokace: **${formatCzechDays(entry.duration_days)}**`,
          `Odblokování: ${toDiscordTimestamp(entry.end_time)}`,
          `Zbývá: **${formatRemainingTime(entry.end_time)}**`
        ].join('\n'),
        inline: false
      }))
    });
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

  async getStatsEmbed(guild, userId) {
    const state = await this.context.database.counting.read();

    if (userId) {
      const stats = state.user_stats[userId];
      const member = guild.members.cache.get(userId) ?? await guild.members.fetch(userId).catch(() => null);

      if (!stats) {
        return createEmbed({
          title: '📊 Statistiky countingu',
          description: `${member ?? 'Tenhle uživatel'} zatím nemá žádné counting statistiky.`,
          color: Colors.Orange
        });
      }

      const correct = stats.correct_counts;
      const wrong = stats.wrong_counts;
      const total = correct + wrong;
      const accuracy = total ? Math.round((correct / total) * 100) : 0;
      const block = state.blocked_users[userId];
      const blockInfo = [];

      if (stats.consecutive_fails > 0) {
        blockInfo.push(`Po sobě jdoucí chyby: **${stats.consecutive_fails}**`);
      }

      if (stats.total_blocks > 0) {
        blockInfo.push(`Počet blokací: **${stats.total_blocks}**`);
      }

      if (block && new Date(block.end_time) > new Date()) {
        blockInfo.push(`Aktuálně blokován do: ${toDiscordTimestamp(block.end_time)}`);
        blockInfo.push(`Zbývá: **${formatRemainingTime(block.end_time)}**`);
      }

      return createEmbed({
        title: `📊 Statistiky countingu - ${member?.displayName ?? stats.username}`,
        description: 'Podrobné statistiky uživatele v countingu.',
        color: Colors.Blue,
        thumbnail: member?.displayAvatarURL?.(),
        footer: `Rekord serveru: ${state.high_score}`,
        fields: [
          {
            name: 'Základní statistiky',
            value: [
              `Správné počty: **${correct}**`,
              `Chybné počty: **${wrong}**`,
              `Celkem pokusů: **${total}**`,
              `Přesnost: **${accuracy}%**`
            ].join('\n'),
            inline: false
          },
          ...(blockInfo.length ? [{
            name: 'Blokace a chyby',
            value: blockInfo.join('\n'),
            inline: false
          }] : []),
          {
            name: 'Pravidla blokování',
            value: [
              'První blokace po 5 chybách za sebou.',
              'Další blokace po 2 chybách za sebou.',
              'První blokace trvá 1 den, další 3 dny.'
            ].join('\n'),
            inline: false
          }
        ]
      });
    }

    const stats = await this.getStats();
    if (!stats.length) {
      return createEmbed({
        title: '📊 Statistiky countingu',
        description: 'Zatím nejsou k dispozici žádné counting statistiky.',
        color: Colors.Orange
      });
    }

    const fields = stats.map((entry, index) => {
      const total = entry.correct_counts + entry.wrong_counts;
      const accuracy = total ? Math.round((entry.correct_counts / total) * 100) : 0;
      const block = state.blocked_users[entry.userId];
      const extra = [];

      if (entry.total_blocks > 0) {
        extra.push(`Blokace: **${entry.total_blocks}**`);
      }

      if (block && new Date(block.end_time) > new Date()) {
        extra.push(`⛔ Ještě: **${formatRemainingTime(block.end_time)}**`);
      }

      return {
        name: `${index + 1}. ${entry.username}`,
        value: [
          `Správně: **${entry.correct_counts}**`,
          `Špatně: **${entry.wrong_counts}**`,
          `Přesnost: **${accuracy}%**`,
          ...extra
        ].join('\n'),
        inline: true
      };
    });

    return createEmbed({
      title: '📊 Statistiky countingu',
      description: `Top 10 hráčů | Rekord: **${state.high_score}**`,
      color: Colors.Blue,
      footer: `Celkem failů: ${state.failed_counts}`,
      fields
    });
  }

  getRulesEmbed() {
    return createEmbed({
      title: '📏 Pravidla countingu',
      description: 'Jak funguje counting na serveru.',
      color: Colors.Gold,
      fields: [
        { name: '1. Pořadí', value: 'Počítá se po jedné nahoru.', inline: false },
        { name: '2. Střídání', value: 'Stejný člověk nesmí poslat dvě správná čísla po sobě.', inline: false },
        { name: '3. Chyba', value: 'Špatné číslo nebo špatný výsledek resetuje counting na nulu.', inline: false },
        { name: '4. Formáty', value: 'Povolená jsou celá čísla, `hex`, `bin`, `oct` a bezpečné matematické výrazy.', inline: false },
        { name: '5. Blokace', value: 'Po sérii failů může přijít dočasná blokace z countingu.', inline: false }
      ]
    });
  }

  getFormatsEmbed() {
    return createEmbed({
      title: '🔣 Podporované formáty countingu',
      description: 'Výsledek vždy musí odpovídat dalšímu číslu v pořadí.',
      color: Colors.LightGrey,
      fields: [
        { name: 'Desítková čísla', value: '`255`', inline: false },
        { name: 'Hexadecimal', value: '`0xFF`', inline: true },
        { name: 'Binární', value: '`0b11111111`', inline: true },
        { name: 'Osmičková', value: '`0o377`', inline: true },
        { name: 'Výrazy', value: '`(2 + 3) * 5`', inline: false }
      ]
    });
  }

  async getChannelEmbed() {
    const config = await this.context.configStore.get();
    return createEmbed({
      title: '📍 Counting kanál',
      description: `Aktivní counting kanál je ${mentionChannel(config.counting.channelId)}.`,
      color: Colors.Blurple
    });
  }
}
