import { ActivityType, ChannelType, Colors } from 'discord.js';
import { createEmbed, fetchTextChannel } from '../../shared/discord-helpers.js';
import { chunkArray, formatDuration, mentionChannel, mentionRole } from '../../shared/utils.js';

export class UtilityService {
  constructor(context) {
    this.context = context;
  }

  async getUptimeResponse() {
    const uptime = Date.now() - this.context.startedAt.getTime();

    return {
      embeds: [
        createEmbed({
          title: 'Uptime',
          description: `Bot běží ${formatDuration(uptime)}.`
        })
      ]
    };
  }

  async createInvite(interaction) {
    const config = await this.context.configStore.get();
    const targetChannel = await fetchTextChannel(interaction.guild, config.guild.welcomeChannelId) ?? interaction.channel;

    if (!targetChannel || targetChannel.type !== ChannelType.GuildText) {
      throw new Error('Nepodařilo se najít textový kanál pro invite.');
    }

    const invite = await targetChannel.createInvite({
      maxAge: config.discord.inviteMaxAgeSeconds,
      maxUses: config.discord.inviteMaxUses,
      unique: false,
      reason: `Slash command od ${interaction.user.tag}`
    });

    return {
      embeds: [
        createEmbed({
          title: 'Pozvanka',
          description: invite.url
        })
      ]
    };
  }

  async getCommandListResponse(commands, includeAdmin) {
    const grouped = new Map();

    for (const command of commands) {
      if (command.meta.hidden) {
        continue;
      }

      if (!includeAdmin && command.meta.adminOnly) {
        continue;
      }

      const bucket = grouped.get(command.meta.category) ?? [];
      bucket.push(`/${command.data.name} - ${command.data.description}`);
      grouped.set(command.meta.category, bucket);
    }

    const embeds = [];

    for (const [category, items] of grouped.entries()) {
      const chunks = chunkArray(items, 12);

      for (const [index, chunk] of chunks.entries()) {
        embeds.push(createEmbed({
          title: index === 0 ? `Příkazy: ${category}` : `Příkazy: ${category} (${index + 1})`,
          description: chunk.join('\n')
        }));
      }
    }

    return { embeds };
  }

  buildRulesEmbed(config) {
    return createEmbed({
      title: 'Serverová pravidla',
      color: Colors.Orange,
      description: config.discord.rules.map((rule, index) => `${index + 1}. ${rule}`).join('\n') || 'Pravidla ještě nejsou vyplněna.',
      fields: [
        {
          name: 'AI systém',
          value: [
            `Model: \`${config.ai.model}\``,
            `Batch: \`${config.ai.messagesBatch}\``,
            `Kanály: ${config.ai.moderationChannelIds.map(mentionChannel).join(', ') || 'nenastaveno'}`,
            `Pozitivní prahy: ${config.ai.positiveThresholds.join(' / ')}`,
            `Negativní role: ${mentionRole(config.ai.negativeRoleId)}`
          ].join('\n')
        }
      ]
    });
  }

  async getRulesResponse() {
    const config = await this.context.configStore.get();
    return {
      embeds: [this.buildRulesEmbed(config)]
    };
  }

  async publishRules(channelId, messageId) {
    const config = await this.context.configStore.get();
    const guild = this.context.client.guilds.cache.get(this.context.guildId);
    const channel = await fetchTextChannel(guild, channelId || config.guild.welcomeChannelId);

    if (!channel) {
      throw new Error('Nenašel jsem kanál pro pravidla.');
    }

    const embed = this.buildRulesEmbed(config);

    if (messageId) {
      const message = await channel.messages.fetch(messageId);
      await message.edit({ embeds: [embed] });
      return message;
    }

    return channel.send({ embeds: [embed] });
  }

  async setPresence() {
    const config = await this.context.configStore.get();
    const texts = config.discord.activityTexts.filter(Boolean);

    if (!texts.length) {
      return;
    }

    const guild = this.context.client.guilds.cache.get(this.context.guildId);
    const memberCount = guild?.memberCount ?? 0;
    const index = this.context.runtime.currentActivityIndex % texts.length;
    const template = texts[index];
    const status = template.replaceAll('{count}', String(memberCount));

    this.context.runtime.currentActivityIndex = (index + 1) % texts.length;

    await this.context.client.user.setPresence({
      activities: [
        {
          type: ActivityType.Watching,
          name: status
        }
      ],
      status: 'online'
    });
  }
}

export class SetupService {
  constructor(context) {
    this.context = context;
  }

  async ensureCategory(guild, config) {
    const name = config.setup.categoryName;
    const existing = guild.channels.cache.find(
      (channel) => channel.type === ChannelType.GuildCategory && channel.name === name
    );

    if (existing) {
      return existing;
    }

    return guild.channels.create({
      name,
      type: ChannelType.GuildCategory
    });
  }

  async createManagedChannel(guild, configKey, nameOverride) {
    const config = await this.context.configStore.get();
    const category = await this.ensureCategory(guild, config);
    const name = nameOverride || config.setup.channelNames[configKey];
    const channel = await guild.channels.create({
      name,
      type: ChannelType.GuildText,
      parent: category.id
    });

    await this.context.configStore.update((current) => {
      if (configKey === 'youtube') {
        current.youtube.notificationChannelId = channel.id;
      } else if (configKey === 'counting') {
        current.counting.channelId = channel.id;
      } else if (configKey === 'summary') {
        current.summary.targetChannelId = channel.id;
      } else if (configKey === 'audit') {
        current.audit.channelId = channel.id;
      }

      return current;
    });

    return channel;
  }

  async applyBasePermissions(guild) {
    const config = await this.context.configStore.get();
    const everyone = guild.roles.everyone;
    const tasks = [];

    const youtubeChannel = await fetchTextChannel(guild, config.youtube.notificationChannelId);
    if (youtubeChannel) {
      tasks.push(youtubeChannel.permissionOverwrites.edit(everyone, { SendMessages: false }));
    }

    const summaryChannel = await fetchTextChannel(guild, config.summary.targetChannelId);
    if (summaryChannel) {
      tasks.push(summaryChannel.permissionOverwrites.edit(everyone, { SendMessages: false }));
    }

    const welcomeChannel = await fetchTextChannel(guild, config.guild.welcomeChannelId);
    if (welcomeChannel) {
      tasks.push(welcomeChannel.permissionOverwrites.edit(everyone, { SendMessages: false }));
    }

    const countingChannel = await fetchTextChannel(guild, config.counting.channelId);
    if (countingChannel) {
      tasks.push(countingChannel.setRateLimitPerUser(config.counting.slowmodeSeconds));
    }

    await Promise.all(tasks);
  }

  async setAuditChannel(channelId) {
    return this.context.configStore.update((current) => {
      current.audit.channelId = channelId;
      return current;
    });
  }

  changeLogLevel(level) {
    this.context.logger.level = level;
  }
}
