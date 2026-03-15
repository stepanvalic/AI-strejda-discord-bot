import type { Message } from "discord.js";
import type { Logger } from "pino";

import type { BotConfig } from "../../config/types.js";

export class SummaryService {
  constructor(
    private readonly config: BotConfig,
    private readonly logger: Logger,
  ) {}

  buildRulesLines(): string[] {
    return [
      `Provider: ${this.config.summary.provider}`,
      `Model: ${this.config.summary.deepseekModel}`,
      `Cooldown: ${this.config.summary.cooldownHours} h`,
      `Zdrojovy chat: ${
        this.config.channels.summaryChatId ? `<#${this.config.channels.summaryChatId}>` : "neni nastaven"
      }`,
      `Vystupni kanal: ${
        this.config.channels.summaryChannelId ? `<#${this.config.channels.summaryChannelId}>` : "neni nastaven"
      }`,
      "Automat ma bezet denne ve 03:00.",
    ];
  }

  async handleMessageCreate(_message: Message): Promise<void> {
    this.logger.debug("Summary message hook wired");
  }
}
