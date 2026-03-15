import type { Message, PartialMessage } from "discord.js";
import type { Logger } from "pino";

import type { BotConfig } from "../../config/types.js";

export class CountingService {
  constructor(
    private readonly config: BotConfig,
    private readonly logger: Logger,
  ) {}

  getRules(): string[] {
    return [
      "Pise se vzestupna rada po jedne.",
      "Nikdo nesmi dat dve spravna cisla po sobe.",
      "Chyba resetuje count na 0.",
      "Nevalidni text se maze.",
      "Blokace za fail streaky musi prezit restart.",
    ];
  }

  getSupportedFormats(): string[] {
    return [
      "Decimal: 42",
      "Hex: 0x2A",
      "Binary: 0b101010",
      "Octal: 0o52",
      "Vyrazy: (40 + 2)",
    ];
  }

  getChannelMention(): string {
    return this.config.channels.countingChannelId
      ? `<#${this.config.channels.countingChannelId}>`
      : "neni nastaveny";
  }

  async handleMessageCreate(_message: Message): Promise<void> {
    this.logger.debug("Counting message hook wired");
  }

  async handleMessageUpdate(_oldMessage: Message | PartialMessage, _newMessage: Message | PartialMessage): Promise<void> {
    this.logger.debug("Counting message update hook wired");
  }

  async handleMessageDelete(_message: Message | PartialMessage): Promise<void> {
    this.logger.debug("Counting message delete hook wired");
  }
}
