import { ChannelType } from "discord.js";

import { createGroupCommand } from "./support/group-command.js";
import { replyPlanned } from "./support/response.js";

export const summaryCommand = createGroupCommand({
  name: "summary",
  description: "Daily summary a on-demand shrnuti.",
  category: "Summary",
  subcommands: [
    {
      name: "den",
      description: "Vygeneruje denni shrnuti konkretniho dne.",
      adminOnly: true,
      configure: (builder) =>
        builder
          .addStringOption((option) =>
            option
              .setName("datum")
              .setDescription("Datum ve formatu DD/MM/YYYY")
              .setRequired(false),
          )
          .addChannelOption((option) =>
            option
              .setName("kanal")
              .setDescription("Volitelny cilovy kanal")
              .setRequired(false)
              .addChannelTypes(ChannelType.GuildText),
          )
          .addBooleanOption((option) =>
            option
              .setName("pregenerovat")
              .setDescription("Pregenerovat i kdyz uz shrnuti existuje")
              .setRequired(false),
          ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Daily summary", [
          `Datum: ${interaction.options.getString("datum") ?? "vcerejsek"}`,
          `Cilovy kanal: ${interaction.options.getChannel("kanal") ?? "default summary kanal"}`,
          `Pregenerovat: ${interaction.options.getBoolean("pregenerovat") ?? false}`,
          "Chybi summary store a DeepSeek client.",
        ]);
      },
    },
    {
      name: "dm-posledni",
      description: "Posle DM shrnuti poslednich N zprav.",
      configure: (builder) =>
        builder.addIntegerOption((option) =>
          option
            .setName("pocet-zprav")
            .setDescription("Pocet zprav 10-500")
            .setRequired(true)
            .setMinValue(10)
            .setMaxValue(500),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "DM summary", [
          `Pocet zprav: ${interaction.options.getInteger("pocet-zprav", true)}`,
          "Flow ma respektovat user cooldown a admin bypass.",
          "Chybi summary message store a AI provider.",
        ], false);
      },
    },
    {
      name: "pocet-zprav",
      description: "Ukaze pocet ulozenych zprav za dnesek.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Summary message count", [
          "Prikaz ma pocitat dnesni zpravy ze summary chatu.",
          "Chybi perzistentni summary message store.",
          ...context.services.summary.buildRulesLines(),
        ]);
      },
    },
  ],
});
