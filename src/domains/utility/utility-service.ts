import { ChannelType, EmbedBuilder, type Guild, type TextChannel } from "discord.js";

import type { BotConfig } from "../../config/types.js";
import type { CommandCatalogEntry } from "../../discord/commands/types.js";
import { formatDuration } from "../../shared/time/format-duration.js";

const humanizeYoutubeChannel = (channelId?: string): string | undefined => {
  if (!channelId) {
    return undefined;
  }

  if (channelId.startsWith("@")) {
    return `https://www.youtube.com/${channelId}`;
  }

  return `https://www.youtube.com/channel/${channelId}`;
};

export class UtilityService {
  constructor(
    private readonly config: BotConfig,
    private readonly startedAt: Date,
  ) {}

  getYoutubeChannelUrl(): string | undefined {
    return this.config.youtube.channelUrl ?? humanizeYoutubeChannel(this.config.youtube.channelId);
  }

  getYoutubeNotificationChannelMention(): string {
    return this.config.channels.youtubeNotificationChannelId
      ? `<#${this.config.channels.youtubeNotificationChannelId}>`
      : "neni nastaveny";
  }

  getCountingChannelMention(): string {
    return this.config.channels.countingChannelId
      ? `<#${this.config.channels.countingChannelId}>`
      : "neni nastaveny";
  }

  getUptimeText(): string {
    return formatDuration(Date.now() - this.startedAt.getTime());
  }

  async createInvite(guild: Guild, fallbackChannel: TextChannel): Promise<string> {
    const targetChannelId = this.config.channels.welcomeChannelId ?? fallbackChannel.id;
    const fetched = await guild.channels.fetch(targetChannelId).catch(() => null);

    const targetChannel =
      fetched && fetched.type === ChannelType.GuildText && "createInvite" in fetched
        ? fetched
        : fallbackChannel;

    const invite = await targetChannel.createInvite({
      maxAge: this.config.discord.inviteMaxAge,
      maxUses: this.config.discord.inviteMaxUses,
      unique: false,
      reason: "Slash command /utility invite",
    });

    return invite.url;
  }

  buildCatalogEmbeds(entries: CommandCatalogEntry[], includeAdmin: boolean): EmbedBuilder[] {
    const grouped = entries
      .filter((entry) => entry.listed)
      .filter((entry) => includeAdmin || !entry.adminOnly)
      .reduce<Map<string, CommandCatalogEntry[]>>((map, entry) => {
        const bucket = map.get(entry.category) ?? [];
        bucket.push(entry);
        map.set(entry.category, bucket);
        return map;
      }, new Map());

    return [...grouped.entries()].map(([category, categoryEntries]) => {
      const lines = categoryEntries
        .sort((left, right) => left.path.localeCompare(right.path))
        .map((entry) => {
          const adminTag = entry.adminOnly ? " [admin]" : "";
          return `\`${entry.path}\`${adminTag} - ${entry.description}`;
        });

      return new EmbedBuilder()
        .setColor(this.config.branding.embedColor)
        .setTitle(`Commandy: ${category}`)
        .setDescription(lines.join("\n"))
        .setFooter({ text: this.config.branding.footerText })
        .setTimestamp();
    });
  }

  buildRulesEmbed(): EmbedBuilder {
    const aiThresholds = this.config.ai.positiveThresholds
      .map((threshold, index) => `Role ${index + 1}: ${threshold}`)
      .join("\n");

    return new EmbedBuilder()
      .setColor(this.config.branding.embedColor)
      .setTitle("Serverova pravidla")
      .setDescription(this.config.texts.serverRules.map((rule, index) => `${index + 1}. ${rule}`).join("\n"))
      .addFields(
        {
          name: "AI system",
          value: [
            `Model: ${this.config.ai.model}`,
            `Batch: ${this.config.ai.messagesBatch}`,
            `Interval: ${this.config.ai.moderationIntervalMinutes} min`,
            `Pozitivni prahy:\n${aiThresholds}`,
            `Negativni prah: ${this.config.ai.negativeThreshold}`,
          ].join("\n"),
        },
        {
          name: "Summary",
          value: `Provider: ${this.config.summary.provider}\nCooldown: ${this.config.summary.cooldownHours} h`,
        },
      )
      .setFooter({ text: this.config.branding.footerText })
      .setTimestamp();
  }
}
