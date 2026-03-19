import { Colors } from 'discord.js';
import { createEmbed } from '../../shared/discord-helpers.js';
import { parseDurationInput } from '../../shared/parsers.js';

const DISCORD_TIMEOUT_LIMIT_MS = 28 * 24 * 60 * 60 * 1000;

export class ModerationService {
  constructor(context) {
    this.context = context;
  }

  async timeout(member, durationInput, reason, moderator) {
    if (member.permissions.has('Administrator')) {
      throw new Error('Admina timeoutnout nejde.');
    }

    const durationMs = Math.min(parseDurationInput(durationInput), DISCORD_TIMEOUT_LIMIT_MS);
    await member.timeout(durationMs, reason || `Slash timeout od ${moderator.tag}`);
    await member.send(`Dostal jsi timeout na ${Math.round(durationMs / 60000)} minut. Důvod: ${reason || 'neuveden'}`).catch(() => null);
    this.context.internalEvents.emit('audit:moderation', {
      type: 'timeout',
      targetId: member.id,
      moderatorId: moderator.id,
      reason,
      durationMs
    });

    return createEmbed({
      title: 'Timeout udělen',
      color: Colors.Orange,
      description: `${member} dostal timeout.`,
      fields: [
        { name: 'Délka', value: `${Math.round(durationMs / 60000)} minut`, inline: true },
        { name: 'Důvod', value: reason || 'neuveden', inline: true }
      ]
    });
  }

  async untimeout(member, reason, moderator) {
    await member.timeout(null, reason || `Slash untimeout od ${moderator.tag}`);
    this.context.internalEvents.emit('audit:moderation', {
      type: 'untimeout',
      targetId: member.id,
      moderatorId: moderator.id,
      reason
    });

    return createEmbed({
      title: 'Timeout zrušen',
      color: Colors.Green,
      description: `${member} už zase může dýchat.`
    });
  }

  async ban(member, reason, moderator) {
    if (member.permissions.has('Administrator')) {
      throw new Error('Admina zabanovat nejde.');
    }

    await member.send(`Dostal jsi ban. Důvod: ${reason || 'neuveden'}`).catch(() => null);
    await member.ban({ reason: reason || `Slash ban od ${moderator.tag}` });
    this.context.internalEvents.emit('audit:moderation', {
      type: 'ban',
      targetId: member.id,
      moderatorId: moderator.id,
      reason
    });

    return createEmbed({
      title: 'Ban udělen',
      color: Colors.Red,
      description: `${member.user.tag} dostal ban.`,
      fields: [{ name: 'Důvod', value: reason || 'neuveden' }]
    });
  }

  async unban(guild, userId, reason, moderator) {
    const user = await guild.client.users.fetch(userId);
    await guild.members.unban(user, reason || `Slash unban od ${moderator.tag}`);
    this.context.internalEvents.emit('audit:moderation', {
      type: 'unban',
      targetId: user.id,
      moderatorId: moderator.id,
      reason
    });

    return createEmbed({
      title: 'Ban zrušen',
      color: Colors.Green,
      description: `${user.tag} byl odbanován.`
    });
  }
}
