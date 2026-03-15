import type { Message } from "discord.js";
import type { Logger } from "pino";

export class WordFilterService {
  constructor(private readonly logger: Logger) {}

  async handleMessageCreate(_message: Message): Promise<void> {
    this.logger.debug("Word filter hook wired");
  }
}
