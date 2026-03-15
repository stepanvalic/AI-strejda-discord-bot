import { loadConfig } from "../config/load-config.js";
import { slashCommands } from "../discord/commands/index.js";
import { registerGuildSlashCommands } from "../discord/register-slash-commands.js";
import { createLogger } from "../infrastructure/logging/create-logger.js";

const main = async () => {
  const config = await loadConfig();
  const logger = createLogger(config);
  await registerGuildSlashCommands(config, slashCommands, logger);
};

main().catch((error) => {
  console.error("Slash registration failed", error);
  process.exitCode = 1;
});
