import type { Guild, GuildMember, User } from "discord.js";
import { PermissionsBitField } from "discord.js";
import type { Logger } from "pino";

import { clampTimeoutDuration, parseDurationInput } from "../../shared/time/parse-duration.js";

const isAdminMember = (member: GuildMember): boolean =>
  member.permissions.has(PermissionsBitField.Flags.Administrator);

const sendBestEffortDm = async (user: User, content: string) => {
  await user.send(content).catch(() => undefined);
};

export class ModerationService {
  constructor(private readonly logger: Logger) {}

  async timeout(member: GuildMember, durationInput?: string, reason?: string): Promise<number> {
    if (isAdminMember(member)) {
      throw new Error("Admina timeoutnout nejde.");
    }

    const duration = clampTimeoutDuration(parseDurationInput(durationInput));
    await member.timeout(duration, reason ?? "Slash command /moderation timeout");
    await sendBestEffortDm(
      member.user,
      `Dostal jsi timeout na ${Math.round(duration / 60_000)} minut. Duvod: ${reason ?? "neuveden"}.`,
    );

    this.logger.info({ memberId: member.id, duration, reason }, "Member timed out");
    return duration;
  }

  async untimeout(member: GuildMember, reason?: string): Promise<void> {
    await member.timeout(null, reason ?? "Slash command /moderation untimeout");
    await sendBestEffortDm(
      member.user,
      `Timeout ti byl zrusen. Duvod: ${reason ?? "neuveden"}.`,
    );

    this.logger.info({ memberId: member.id, reason }, "Member timeout cleared");
  }

  async ban(member: GuildMember, reason?: string): Promise<void> {
    if (isAdminMember(member)) {
      throw new Error("Admina zabanovat nejde.");
    }

    await sendBestEffortDm(
      member.user,
      `Byl jsi zabanovan. Duvod: ${reason ?? "neuveden"}.`,
    );

    await member.ban({ reason: reason ?? "Slash command /moderation ban" });
    this.logger.info({ memberId: member.id, reason }, "Member banned");
  }

  async unban(guild: Guild, userId: string, reason?: string): Promise<void> {
    await guild.members.unban(userId, reason ?? "Slash command /moderation unban");
    this.logger.info({ userId, reason }, "Member unbanned");
  }
}
