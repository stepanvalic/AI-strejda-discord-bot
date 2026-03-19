import { Colors } from 'discord.js';
import { createEmbed, fetchTextChannel } from '../../shared/discord-helpers.js';

export class WelcomeService {
  constructor(context) {
    this.context = context;
  }

  async ensureDefaultRole(member) {
    const config = await this.context.configStore.get();

    if (!config.guild.defaultRoleId || member.user.bot) {
      return false;
    }

    if (member.roles.cache.has(config.guild.defaultRoleId)) {
      return false;
    }

    await member.roles.add(config.guild.defaultRoleId, 'Default role při welcome flow');
    return true;
  }

  async sendWelcome(member) {
    const config = await this.context.configStore.get();
    const channel = await fetchTextChannel(member.guild, config.guild.welcomeChannelId);

    if (!channel) {
      return null;
    }

    return channel.send({
      embeds: [
        createEmbed({
          title: 'Nový člověk v baráku',
          color: Colors.Green,
          description: `Vítej ${member}.\nDiscord ID: \`${member.id}\``,
          fields: [
            {
              name: 'Účet',
              value: member.user.tag
            }
          ]
        }).setThumbnail(member.displayAvatarURL())
      ]
    });
  }

  async rewelcome(member) {
    const roleAdded = await this.ensureDefaultRole(member);
    const message = await this.sendWelcome(member);
    return { roleAdded, message };
  }

  async backfillDefaultRole(guild) {
    await guild.members.fetch();
    const report = {
      scanned: 0,
      added: 0,
      skippedBots: 0,
      failed: 0
    };

    for (const member of guild.members.cache.values()) {
      if (member.user.bot) {
        report.skippedBots += 1;
        continue;
      }

      report.scanned += 1;

      try {
        const changed = await this.ensureDefaultRole(member);
        if (changed) {
          report.added += 1;
        }
      } catch {
        report.failed += 1;
      }
    }

    return report;
  }
}
