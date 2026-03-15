import type { Guild } from "discord.js";
import type { Logger } from "pino";

import type { LogLevel } from "../../config/types.js";

export class SetupService {
  constructor(private readonly logger: Logger) {}

  setLogLevel(level: LogLevel): void {
    this.logger.level = level;
  }

  async dryRunCreateChannel(_guild: Guild, name: string): Promise<string> {
    this.logger.info({ channelName: name }, "Setup channel creation placeholder");
    return `Kanal \`${name}\` ma pripraveny slash command, ale trvala perzistence do configu se dodela v dalsim kroku.`;
  }
}
