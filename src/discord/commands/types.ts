import type { ChatInputCommandInteraction, SlashCommandBuilder } from "discord.js";

import type { AppContext } from "../../app/context.js";

export interface CommandCatalogEntry {
  path: string;
  description: string;
  category: string;
  adminOnly: boolean;
  listed: boolean;
}

export interface SlashCommandModule {
  name: string;
  data: SlashCommandBuilder;
  helpEntries: CommandCatalogEntry[];
  execute(interaction: ChatInputCommandInteraction, context: AppContext): Promise<void>;
}
