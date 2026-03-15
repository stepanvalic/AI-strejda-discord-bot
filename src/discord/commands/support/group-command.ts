import {
  SlashCommandBuilder,
  type ChatInputCommandInteraction,
  type SlashCommandSubcommandBuilder,
} from "discord.js";

import type { AppContext } from "../../../app/context.js";
import type { CommandCatalogEntry, SlashCommandModule } from "../types.js";
import { hasAdminPermission } from "./permissions.js";
import { createBaseEmbed, replyWithEmbed } from "./response.js";

export interface GroupSubcommandSpec {
  name: string;
  description: string;
  adminOnly?: boolean;
  listed?: boolean;
  configure?: (builder: SlashCommandSubcommandBuilder) => SlashCommandSubcommandBuilder;
  execute: (interaction: ChatInputCommandInteraction, context: AppContext) => Promise<void>;
}

export interface GroupCommandSpec {
  name: string;
  description: string;
  category: string;
  subcommands: GroupSubcommandSpec[];
}

const buildCatalogEntries = (spec: GroupCommandSpec): CommandCatalogEntry[] =>
  spec.subcommands.map((subcommand) => ({
    path: `/${spec.name} ${subcommand.name}`,
    description: subcommand.description,
    category: spec.category,
    adminOnly: subcommand.adminOnly ?? false,
    listed: subcommand.listed ?? true,
  }));

export const createGroupCommand = (spec: GroupCommandSpec): SlashCommandModule => {
  const data = new SlashCommandBuilder()
    .setName(spec.name)
    .setDescription(spec.description)
    .setDMPermission(false);

  for (const subcommand of spec.subcommands) {
    data.addSubcommand((builder) => {
      builder.setName(subcommand.name).setDescription(subcommand.description);
      return subcommand.configure ? subcommand.configure(builder) : builder;
    });
  }

  return {
    name: spec.name,
    data,
    helpEntries: buildCatalogEntries(spec),
    execute: async (interaction, context) => {
      const subcommandName = interaction.options.getSubcommand();
      const target = spec.subcommands.find((item) => item.name === subcommandName);

      if (!target) {
        const embed = createBaseEmbed(
          context,
          "Neznamy subcommand",
          `Subcommand \`${subcommandName}\` neni pro \`/${spec.name}\` zaregistrovany.`,
        );
        await replyWithEmbed(interaction, embed, true);
        return;
      }

      if (target.adminOnly && !hasAdminPermission(interaction)) {
        const embed = createBaseEmbed(
          context,
          "Pristup zamitnut",
          "Tenhle subcommand je jen pro adminy se serverovymi opravnenimi.",
        );
        await replyWithEmbed(interaction, embed, true);
        return;
      }

      await target.execute(interaction, context);
    },
  };
};
