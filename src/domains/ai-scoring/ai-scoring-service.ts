import type { Message } from "discord.js";
import type { Logger } from "pino";

import type { BotConfig } from "../../config/types.js";

export class AiScoringService {
  constructor(
    private readonly config: BotConfig,
    private readonly logger: Logger,
  ) {}

  buildRulesLines(): string[] {
    return [
      `Model: ${this.config.ai.model}`,
      `Batch size: ${this.config.ai.messagesBatch}`,
      `Interval: ${this.config.ai.moderationIntervalMinutes} min`,
      `Moderovane kanaly: ${
        this.config.ai.moderationChannelIds.length > 0
          ? this.config.ai.moderationChannelIds.map((channelId) => `<#${channelId}>`).join(", ")
          : "neni nastaveno"
      }`,
      `Pozitivni prahy: ${this.config.ai.positiveThresholds.join(", ")}`,
      `Negativni prah: ${this.config.ai.negativeThreshold}`,
      `Velmi negativni prah: ${this.config.ai.veryNegativeThreshold}`,
      `Extra penalizace: ${this.config.ai.negativePenalty}`,
    ];
  }

  async handleMessageCreate(_message: Message): Promise<void> {
    this.logger.debug("AI scoring message hook wired");
  }
}
