import { REST, Routes } from "discord.js";
import type { Logger } from "pino";

import type { BotConfig } from "../config/types.js";
import type { SlashCommandModule } from "./commands/types.js";

export const registerGuildSlashCommands = async (
  config: BotConfig,
  commands: SlashCommandModule[],
  logger: Logger,
) => {
  const rest = new REST({ version: "10" }).setToken(config.discord.token);
  const payload = commands.map((command) => command.data.toJSON());

  await rest.put(
    Routes.applicationGuildCommands(config.discord.applicationId, config.discord.guildId),
    { body: payload },
  );

  logger.info({ commandCount: payload.length }, "Guild slash commands registered");
};
