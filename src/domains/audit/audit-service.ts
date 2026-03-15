import type {
  GuildAuditLogsEntry,
  GuildBan,
  GuildChannel,
  GuildMember,
  Message,
  PartialMessage,
  Role,
} from "discord.js";
import type { Logger } from "pino";

export class AuditService {
  constructor(private readonly logger: Logger) {}

  async handleMessageUpdate(_oldMessage: Message | PartialMessage, _newMessage: Message | PartialMessage): Promise<void> {
    this.logger.debug("Audit message update hook wired");
  }

  async handleMessageDelete(_message: Message | PartialMessage): Promise<void> {
    this.logger.debug("Audit message delete hook wired");
  }

  async handleGuildMemberUpdate(_oldMember: GuildMember, _newMember: GuildMember): Promise<void> {
    this.logger.debug("Audit guild member update hook wired");
  }

  async handleChannelCreate(_channel: GuildChannel): Promise<void> {
    this.logger.debug("Audit channel create hook wired");
  }

  async handleChannelDelete(_channel: GuildChannel): Promise<void> {
    this.logger.debug("Audit channel delete hook wired");
  }

  async handleChannelUpdate(_oldChannel: GuildChannel, _newChannel: GuildChannel): Promise<void> {
    this.logger.debug("Audit channel update hook wired");
  }

  async handleGuildBanAdd(_ban: GuildBan): Promise<void> {
    this.logger.debug("Audit ban add hook wired");
  }

  async handleGuildBanRemove(_ban: GuildBan): Promise<void> {
    this.logger.debug("Audit ban remove hook wired");
  }

  async handleRoleCreate(_role: Role): Promise<void> {
    this.logger.debug("Audit role create hook wired");
  }

  async handleRoleDelete(_role: Role): Promise<void> {
    this.logger.debug("Audit role delete hook wired");
  }

  async handleRoleUpdate(_oldRole: Role, _newRole: Role): Promise<void> {
    this.logger.debug("Audit role update hook wired");
  }

  async handleCustomAuditEvent(_entry: GuildAuditLogsEntry | null): Promise<void> {
    this.logger.debug({ hasEntry: Boolean(_entry) }, "Custom audit entry hook wired");
  }
}
