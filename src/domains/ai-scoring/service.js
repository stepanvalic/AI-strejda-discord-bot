import { Colors } from 'discord.js';
import { createEmbed, isAdminMember } from '../../shared/discord-helpers.js';
import { mentionRole } from '../../shared/utils.js';

function ensureAiUser(store, user) {
  if (!store.users[user.id]) {
    store.users[user.id] = {
      username: user.username,
      positive_score: 0,
      negative_score: 0,
      total_score: 0,
      messages_analyzed: 0,
      last_analyzed: null,
      timeout_count: 0,
      last_timeout: null,
      has_positive_role_1: false,
      has_positive_role_2: false,
      has_positive_role_3: false,
      has_negative_role: false,
      last_role_update_1: null,
      last_role_update_2: null,
      last_role_update_3: null,
      last_negative_role_update: null
    };
  }

  return store.users[user.id];
}

export class AiScoringService {
  constructor(context) {
    this.context = context;
  }

  async resolveDisplayName(guild, entry) {
    const cachedMember = guild?.members?.cache?.get(entry.userId);
    if (cachedMember) {
      return cachedMember.displayName;
    }

    const fetchedMember = guild ? await guild.members.fetch(entry.userId).catch(() => null) : null;
    if (fetchedMember) {
      return fetchedMember.displayName;
    }

    return entry.username || `Uživatel ${entry.userId}`;
  }

  async handleMessage(message) {
    const config = await this.context.configStore.get();

    if (
      !config.features.ai ||
      !config.ai.enabled ||
      !message.guild ||
      message.author.bot ||
      !config.ai.moderationChannelIds.includes(message.channelId) ||
      message.content.startsWith('/') ||
      /^https?:\/\//u.test(message.content.trim())
    ) {
      return false;
    }

    const bucket = this.context.runtime.aiBuffers.get(message.author.id) ?? [];
    bucket.push({
      content: message.content,
      messageId: message.id,
      channelId: message.channelId
    });
    this.context.runtime.aiBuffers.set(message.author.id, bucket);

    if (bucket.length < config.ai.messagesBatch) {
      return false;
    }

    const batch = bucket.splice(0, config.ai.messagesBatch);
    const result = await this.analyzeBatch(batch.map((entry) => entry.content), config.ai.model);
    await this.context.database.aiModeration.update((store) => {
      const userRecord = ensureAiUser(store, message.author);
      userRecord.username = message.author.username;
      userRecord.positive_score += result.positiveScore;
      userRecord.negative_score += result.negativeScore;
      userRecord.messages_analyzed += batch.length;
      userRecord.last_analyzed = new Date().toISOString();

      if (result.negativeScore >= config.ai.veryNegativeThreshold || result.sentimentScore <= -config.ai.veryNegativeThreshold) {
        userRecord.negative_score += config.ai.negativePenalty;
      }

      userRecord.total_score = userRecord.positive_score - userRecord.negative_score;
      store.last_updated = new Date().toISOString();
      return store;
    });

    if (!isAdminMember(message.member)) {
      await this.syncMemberRoles(message.member);
    }

    return true;
  }

  async analyzeBatch(messages, model) {
    if (!this.context.env.GEMINI_API_KEY) {
      return this.fallbackAnalyze(messages);
    }

    const prompt = [
      'Jsi velmi shovívavý moderátor reputačního systému.',
      'Vrať JSON se sentiment_score, positive_score, negative_score a explanation.',
      'Preferuj pozitivní interpretaci a netrestej zbytečně.',
      'Zprávy:',
      ...messages.map((message, index) => `${index + 1}. ${message}`)
    ].join('\n');

    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${this.context.env.GEMINI_API_KEY}`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        contents: [
          {
            role: 'user',
            parts: [{ text: prompt }]
          }
        ],
        generationConfig: {
          responseMimeType: 'application/json'
        }
      })
    });

    if (!response.ok) {
      this.context.logger.warn({ status: response.status }, 'Gemini vrátil chybu, padám na fallback.');
      return this.fallbackAnalyze(messages);
    }

    const payload = await response.json();
    const text = payload.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!text) {
      return this.fallbackAnalyze(messages);
    }

    const parsed = JSON.parse(text);
    await this.recordTokenUsage('gemini', model, 'moderation', payload.usageMetadata);

    return {
      sentimentScore: Number(parsed.sentiment_score) || 0,
      positiveScore: Number(parsed.positive_score) || 0,
      negativeScore: Number(parsed.negative_score) || 0,
      explanation: parsed.explanation || ''
    };
  }

  fallbackAnalyze(messages) {
    const positiveWords = ['dik', 'dekuji', 'super', 'parada', 'pomohlo', 'dobre'];
    const negativeWords = ['debil', 'idiot', 'buzna', 'retard', 'kokot'];
    const combined = messages.join(' ').toLowerCase();
    const positiveHits = positiveWords.filter((word) => combined.includes(word)).length;
    const negativeHits = negativeWords.filter((word) => combined.includes(word)).length;
    return {
      sentimentScore: (positiveHits - negativeHits) * 20,
      positiveScore: positiveHits * 25,
      negativeScore: negativeHits * 25,
      explanation: 'Fallback heuristika bez Gemini.'
    };
  }

  async recordTokenUsage(provider, model, operation, usageMetadata) {
    if (!usageMetadata) {
      return;
    }

    await this.context.database.tokenUsage.update((store) => {
      store.entries.push({
        timestamp: new Date().toISOString(),
        date: new Date().toISOString().slice(0, 10),
        time: new Date().toISOString().slice(11, 19),
        provider,
        model,
        operation,
        prompt_tokens: usageMetadata.promptTokenCount || 0,
        completion_tokens: usageMetadata.candidatesTokenCount || 0,
        total_tokens: usageMetadata.totalTokenCount || 0,
        cost_usd: 0
      });
      return store;
    });
  }

  async getUserScore(userId) {
    const store = await this.context.database.aiModeration.read();
    return store.users[userId] ?? null;
  }

  async getTopUsers(descending = true) {
    const store = await this.context.database.aiModeration.read();
    return Object.entries(store.users)
      .map(([userId, value]) => ({ userId, ...value }))
      .sort((left, right) => descending ? right.total_score - left.total_score : left.total_score - right.total_score)
      .slice(0, 10);
  }

  async getUserScoreEmbed(user) {
    const score = await this.getUserScore(user.id);
    const config = await this.context.configStore.get();

    if (!score) {
      return createEmbed({
        title: `🤖 AI skóre - ${user.displayName ?? user.username}`,
        description: `${user} zatím nemá žádné AI skóre.`,
        color: Colors.Orange,
        thumbnail: user.displayAvatarURL?.()
      });
    }

    return createEmbed({
      title: `🤖 AI skóre - ${user.displayName ?? user.username}`,
      description: 'Hodnocení chování na základě analýzy zpráv pomocí AI.',
      color: score.total_score >= 0 ? Colors.Blue : Colors.Red,
      thumbnail: user.displayAvatarURL?.(),
      footer: 'AI moderační systém',
      fields: [
        {
          name: 'Celkové skóre',
          value: `**${score.total_score}**`,
          inline: false
        },
        {
          name: 'Pozitivní body',
          value: `**${score.positive_score}**`,
          inline: true
        },
        {
          name: 'Negativní body',
          value: `**${score.negative_score}**`,
          inline: true
        },
        {
          name: 'Analyzovaných zpráv',
          value: `**${score.messages_analyzed}**`,
          inline: true
        },
        {
          name: 'Hranice pro pozitivní role',
          value: config.ai.positiveThresholds
            .map((threshold, index) => `${'🌟'.repeat(index + 1)} Úroveň ${index + 1}: **${threshold}**`)
            .join('\n'),
          inline: false
        },
        {
          name: 'Negativní hranice',
          value: [
            `⚠️ Varování / role: **${config.ai.negativeThreshold}**`,
            `⛔ Velmi negativní práh: **${config.ai.veryNegativeThreshold}**`,
            `🔻 Penalizace navíc: **${config.ai.negativePenalty}**`
          ].join('\n'),
          inline: false
        }
      ]
    });
  }

  async getLeaderboardEmbed(guild, descending = true) {
    const users = await this.getTopUsers(descending);

    if (!users.length) {
      return createEmbed({
        title: descending ? '🏆 AI skóre - Top 10' : '⚠️ AI skóre - Bottom 10',
        description: 'Zatím nejsou k dispozici žádné statistiky AI moderace.',
        color: descending ? Colors.Gold : Colors.Red,
        footer: 'AI moderační systém'
      });
    }

    const fields = [];

    for (const [index, entry] of users.entries()) {
      const displayName = await this.resolveDisplayName(guild, entry);
      fields.push({
        name: `${index + 1}. ${displayName}`,
        value: [
          `Skóre: **${entry.total_score}**`,
          `Pozitivní: **${entry.positive_score}**`,
          `Negativní: **${entry.negative_score}**`,
          `Zprávy: **${entry.messages_analyzed}**`
        ].join('\n'),
        inline: true
      });
    }

    return createEmbed({
      title: descending ? '🏆 AI skóre - Top 10 uživatelů' : '⚠️ AI skóre - Bottom 10 uživatelů',
      description: descending
        ? 'Žebříček uživatelů s nejvyšším AI skóre.'
        : 'Žebříček uživatelů s nejnižším AI skóre.',
      color: descending ? Colors.Gold : Colors.Red,
      footer: 'AI moderační systém',
      fields
    });
  }

  async syncMemberRoles(member) {
    const config = await this.context.configStore.get();
    const store = await this.context.database.aiModeration.read();
    const record = store.users[member.id];

    if (!record) {
      return;
    }

    const checks = [
      { roleId: config.ai.positiveRoleIds[0], active: record.total_score >= config.ai.positiveThresholds[0], flag: 'has_positive_role_1', stamp: 'last_role_update_1' },
      { roleId: config.ai.positiveRoleIds[1], active: record.total_score >= config.ai.positiveThresholds[1], flag: 'has_positive_role_2', stamp: 'last_role_update_2' },
      { roleId: config.ai.positiveRoleIds[2], active: record.total_score >= config.ai.positiveThresholds[2], flag: 'has_positive_role_3', stamp: 'last_role_update_3' },
      { roleId: config.ai.negativeRoleId, active: record.total_score <= config.ai.negativeThreshold, flag: 'has_negative_role', stamp: 'last_negative_role_update' }
    ];

    for (const check of checks) {
      if (!check.roleId) {
        continue;
      }

      const hasRole = member.roles.cache.has(check.roleId);
      if (check.active && !hasRole) {
        await member.roles.add(check.roleId, 'AI score threshold reached');
      }

      if (!check.active && hasRole) {
        await member.roles.remove(check.roleId, 'AI score threshold dropped');
      }
    }

    await this.context.database.aiModeration.update((updatedStore) => {
      const updatedRecord = updatedStore.users[member.id];
      if (!updatedRecord) {
        return updatedStore;
      }

      for (const check of checks) {
        updatedRecord[check.flag] = check.active;
        updatedRecord[check.stamp] = new Date().toISOString();
      }

      return updatedStore;
    });
  }

  async syncAllRoles(guild) {
    await guild.members.fetch();
    let updated = 0;

    for (const member of guild.members.cache.values()) {
      if (member.user.bot || isAdminMember(member)) {
        continue;
      }

      await this.syncMemberRoles(member);
      updated += 1;
    }

    return updated;
  }

  async getRulesEmbed() {
    const config = await this.context.configStore.get();
    return createEmbed({
      title: '🤖 AI pravidla',
      description: 'Aktuální konfigurace AI reputačního systému.',
      color: Colors.Blurple,
      footer: 'AI moderační systém',
      fields: [
        {
          name: 'Základ',
          value: [
            `Model: \`${config.ai.model}\``,
            `Batch size: \`${config.ai.messagesBatch}\``,
            `Kanály: ${config.ai.moderationChannelIds.map((id) => `<#${id}>`).join(', ') || 'nenastaveno'}`
          ].join('\n'),
          inline: false
        },
        {
          name: 'Pozitivní prahy',
          value: config.ai.positiveThresholds
            .map((threshold, index) => `Úroveň ${index + 1}: **${threshold}** (${mentionRole(config.ai.positiveRoleIds[index])})`)
            .join('\n'),
          inline: false
        },
        {
          name: 'Negativní logika',
          value: [
            `Negativní threshold: **${config.ai.negativeThreshold}**`,
            `Velmi negativní threshold: **${config.ai.veryNegativeThreshold}**`,
            `Negativní penalizace: **${config.ai.negativePenalty}**`,
            `Negativní role: ${mentionRole(config.ai.negativeRoleId)}`
          ].join('\n'),
          inline: false
        }
      ]
    });
  }
}
