import { ChannelType } from "discord.js";

import { createGroupCommand } from "./support/group-command.js";
import { createBaseEmbed, replyPlanned, replyWithEmbed } from "./support/response.js";

export const setupCommand = createGroupCommand({
  name: "setup",
  description: "Setup a provozni admin slash commandy.",
  category: "Setup",
  subcommands: [
    {
      name: "vytvor-youtube-kanal",
      description: "Pripravi setup YouTube kanalu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Setup selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await replyPlanned(interaction, context, "Setup YouTube kanalu", [
          await context.services.setup.dryRunCreateChannel(interaction.guild, "youtube"),
          "Docs chce kanal read-only pro bezne uzivatele.",
          "Trvaly zapis channel ID do configu se dodela pozdeji.",
        ]);
      },
    },
    {
      name: "vytvor-counting-kanal",
      description: "Pripravi setup counting kanalu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Setup selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await replyPlanned(interaction, context, "Setup counting kanalu", [
          await context.services.setup.dryRunCreateChannel(interaction.guild, "counting"),
          "Docs chce ulozit channel ID a nastavit prava pozdeji.",
          "Zatim je to bez persistentniho config writeru.",
        ]);
      },
    },
    {
      name: "vytvor-summary-kanal",
      description: "Pripravi setup summary kanalu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Setup selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await replyPlanned(interaction, context, "Setup summary kanalu", [
          await context.services.setup.dryRunCreateChannel(interaction.guild, "summary"),
          "Docs chce read-only summary kanal.",
          "Chybi persist channel ID do konfigurace.",
        ]);
      },
    },
    {
      name: "kompletni",
      description: "Spusti kompletni setup flow.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Kompletni setup", [
          "Top-level slash command je pripraveny pro vice setup kroku za sebou.",
          "Bude volat create channel flows a config persist vrstvu.",
          "Zatim je to vedomy placeholder, ne fake setup.",
        ]);
      },
    },
    {
      name: "vytvor-audit-kanal",
      description: "Pripravi setup audit kanalu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Setup selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await replyPlanned(interaction, context, "Setup audit kanalu", [
          await context.services.setup.dryRunCreateChannel(interaction.guild, "audit-log"),
          "Docs chce audit-only kanal pro admin role.",
          "Chybi ulozeni channel ID do configu.",
        ]);
      },
    },
    {
      name: "nastav-opravneni",
      description: "Pripravi nastaveni opravneni zakladnich kanalu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Nastav opravneni", [
          "YouTube kanal ma byt read-only.",
          "Counting kanal ma mit prava a slowmode.",
          "Welcome a summary kanal maji byt read-only.",
        ]);
      },
    },
    {
      name: "pouzij-audit-kanal",
      description: "Pouzije existujici kanal jako audit log.",
      adminOnly: true,
      configure: (builder) =>
        builder.addChannelOption((option) =>
          option
            .setName("kanal")
            .setDescription("Existujici audit kanal")
            .setRequired(true)
            .addChannelTypes(ChannelType.GuildText),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Audit kanal z existujiciho kanalu", [
          `Vybrany kanal: ${interaction.options.getChannel("kanal", true)}`,
          "Slash command ma zapsat ID jako audit log kanal.",
          "Chybi config persist vrstva.",
        ]);
      },
    },
    {
      name: "log-level",
      description: "Zmeni log level za behu.",
      adminOnly: true,
      configure: (builder) =>
        builder.addStringOption((option) =>
          option
            .setName("uroven")
            .setDescription("Nova uroven loggeru")
            .setRequired(true)
            .addChoices(
              { name: "trace", value: "trace" },
              { name: "debug", value: "debug" },
              { name: "info", value: "info" },
              { name: "warn", value: "warn" },
              { name: "error", value: "error" },
              { name: "fatal", value: "fatal" },
            ),
        ),
      execute: async (interaction, context) => {
        const level = interaction.options.getString("uroven", true) as typeof context.config.logging.level;
        context.services.setup.setLogLevel(level);

        const embed = createBaseEmbed(context, "Log level zmenen", `Logger ted jede na urovni \`${level}\`.`);
        await replyWithEmbed(interaction, embed, true);
      },
    },
  ],
});
