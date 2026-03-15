import { EmbedBuilder, type Guild, type GuildMember, type TextChannel } from "discord.js";
import type { Logger } from "pino";

import type { BotConfig } from "../../config/types.js";

export class WelcomeService {
  constructor(
    private readonly config: BotConfig,
    private readonly logger: Logger,
  ) {}

  private async resolveWelcomeChannel(guild: Guild): Promise<TextChannel | null> {
    if (!this.config.channels.welcomeChannelId) {
      return null;
    }

    const channel = await guild.channels.fetch(this.config.channels.welcomeChannelId).catch(() => null);
    return channel?.isTextBased() && channel.isDMBased() === false ? (channel as TextChannel) : null;
  }

  async ensureDefaultRole(member: GuildMember): Promise<boolean> {
    if (!this.config.roles.defaultRoleId) {
      return false;
    }

    if (member.roles.cache.has(this.config.roles.defaultRoleId)) {
      return false;
    }

    await member.roles.add(this.config.roles.defaultRoleId, "AI Strejda onboarding");
    return true;
  }

  async sendWelcome(member: GuildMember): Promise<{ roleAssigned: boolean; messageSent: boolean }> {
    const roleAssigned = await this.ensureDefaultRole(member).catch((error) => {
      this.logger.warn({ error, memberId: member.id }, "Failed to assign default role");
      return false;
    });

    const channel = await this.resolveWelcomeChannel(member.guild);
    if (!channel) {
      return { roleAssigned, messageSent: false };
    }

    const embed = new EmbedBuilder()
      .setColor(this.config.branding.embedColor)
      .setTitle("Vitej na serveru")
      .setDescription(`${member} dorazil. Bot ted vypada, ze aspon nekdo prisel dobrovolne.`)
      .addFields(
        { name: "Discord ID", value: member.id, inline: true },
        { name: "Display name", value: member.displayName, inline: true },
      )
      .setThumbnail(member.displayAvatarURL())
      .setFooter({ text: this.config.branding.footerText })
      .setTimestamp();

    await channel.send({ embeds: [embed] });
    return { roleAssigned, messageSent: true };
  }

  async assignDefaultRoleToEveryone(guild: Guild): Promise<{ scanned: number; updated: number; skippedBots: number }> {
    if (!this.config.roles.defaultRoleId) {
      return {
        scanned: 0,
        updated: 0,
        skippedBots: 0,
      };
    }

    const members = await guild.members.fetch();
    let updated = 0;
    let skippedBots = 0;

    for (const member of members.values()) {
      if (member.user.bot) {
        skippedBots += 1;
        continue;
      }

      if (!member.roles.cache.has(this.config.roles.defaultRoleId)) {
        await member.roles.add(this.config.roles.defaultRoleId, "AI Strejda default role sync");
        updated += 1;
      }
    }

    return {
      scanned: members.size,
      updated,
      skippedBots,
    };
  }
}
