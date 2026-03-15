import type { Logger } from "pino";

import type { BotConfig } from "../../config/types.js";

export class YoutubeService {
  constructor(
    private readonly config: BotConfig,
    private readonly logger: Logger,
  ) {}

  buildOverviewLines(): string[] {
    return [
      `Channel ID/handle: ${this.config.youtube.channelId ?? "neni nastaveno"}`,
      `Channel URL: ${this.config.youtube.channelUrl ?? "neni nastavena"}`,
      `Polling interval: ${this.config.youtube.checkIntervalSeconds} s`,
      `Nova videa max age: ${this.config.youtube.newVideoMaxAgeHours} h`,
      `Notifikacni kanal: ${
        this.config.channels.youtubeNotificationChannelId
          ? `<#${this.config.channels.youtubeNotificationChannelId}>`
          : "neni nastaven"
      }`,
    ];
  }

  touch(): void {
    this.logger.debug("YouTube service wired");
  }
}
