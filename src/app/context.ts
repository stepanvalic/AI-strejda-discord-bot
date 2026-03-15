import type { Client } from "discord.js";
import type { Logger } from "pino";

import type { BotConfig } from "../config/types.js";
import type { SlashCommandModule } from "../discord/commands/types.js";
import type { DomainServices } from "./services.js";

export interface AppContext {
  client: Client;
  config: BotConfig;
  logger: Logger;
  startedAt: Date;
  commands: SlashCommandModule[];
  services: DomainServices;
}
