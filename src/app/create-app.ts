import { createServices } from "./services.js";
import type { AppContext } from "./context.js";
import { loadConfig } from "../config/load-config.js";
import { slashCommands } from "../discord/commands/index.js";
import { createDiscordClient } from "../discord/create-client.js";
import { registerDiscordEvents } from "../discord/register-events.js";
import { registerGuildSlashCommands } from "../discord/register-slash-commands.js";
import { createLogger } from "../infrastructure/logging/create-logger.js";

export const createApp = async () => {
  const config = await loadConfig();
  const logger = createLogger(config);
  const client = createDiscordClient();
  const startedAt = new Date();
  const services = createServices(config, logger, startedAt);

  const context: AppContext = {
    client,
    config,
    logger,
    startedAt,
    commands: slashCommands,
    services,
  };

  registerDiscordEvents(client, context);

  return {
    context,
    async start() {
      if (config.runtime.autoRegisterSlashCommands) {
        await registerGuildSlashCommands(config, slashCommands, logger);
      }

      await client.login(config.discord.token);
    },
  };
};
