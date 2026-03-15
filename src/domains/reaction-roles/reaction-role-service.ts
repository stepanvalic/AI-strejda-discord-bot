import type { Guild, MessageReaction, PartialMessageReaction } from "discord.js";
import type { Logger } from "pino";

import type { BotConfig } from "../../config/types.js";
import { NotImplementedError } from "../../shared/errors/not-implemented-error.js";

export class ReactionRoleService {
  constructor(
    private readonly config: BotConfig,
    private readonly logger: Logger,
  ) {}

  describeMappings(): string[] {
    if (this.config.texts.reactionRoles.length === 0) {
      return ["Reaction role mappingy jeste nejsou nastavene."];
    }

    return this.config.texts.reactionRoles.map(
      (mapping) => `${mapping.emoji} -> <@&${mapping.roleId}> (${mapping.description})`,
    );
  }

  async syncReactionRoleMessage(_guild: Guild): Promise<void> {
    throw new NotImplementedError("Reaction role sync");
  }

  async handleReactionAdd(
    _reaction: MessageReaction | PartialMessageReaction,
    _user: { id: string },
  ): Promise<void> {
    this.logger.debug("Reaction add received for reaction-role handler");
  }

  async handleReactionRemove(
    _reaction: MessageReaction | PartialMessageReaction,
    _user: { id: string },
  ): Promise<void> {
    this.logger.debug("Reaction remove received for reaction-role handler");
  }
}
