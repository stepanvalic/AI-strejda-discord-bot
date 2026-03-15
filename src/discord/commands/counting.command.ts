import { ChannelType } from "discord.js";

import { createGroupCommand } from "./support/group-command.js";
import { createBaseEmbed, replyPlanned, replyWithEmbed } from "./support/response.js";

export const countingCommand = createGroupCommand({
  name: "counting",
  description: "Slash commandy pro counting kanal a jeho pravidla.",
  category: "Counting",
  subcommands: [
    {
      name: "stav",
      description: "Vypise stav countingu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Counting stav", [
          `Aktualni counting kanal: ${context.services.utility.getCountingChannelMention()}`,
          "Prikaz je pripraveny pro current count, high score a failed counts.",
          "Chybi dopojit perzistentni counting store.",
        ]);
      },
    },
    {
      name: "reset",
      description: "Resetuje current count a posledniho uzivatele.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Counting reset", [
          "Admin slash command je pripraveny.",
          "Reset ma zasahnout current count a last user.",
          "Chybi dopojeni na counting state store.",
        ]);
      },
    },
    {
      name: "blokuj",
      description: "Rucne zablokuje uzivatele v countingu.",
      adminOnly: true,
      configure: (builder) =>
        builder
          .addUserOption((option) =>
            option.setName("clen").setDescription("Clen k blokaci").setRequired(true),
          )
          .addIntegerOption((option) =>
            option.setName("dny").setDescription("Pocet dni blokace").setRequired(true).setMinValue(1),
          ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Counting blokace", [
          `Clen: ${interaction.options.getUser("clen", true)}`,
          `Dny: ${interaction.options.getInteger("dny", true)}`,
          "Prikaz ma pozdeji overovat admin bypass a duplikat blokace.",
        ]);
      },
    },
    {
      name: "blokovani",
      description: "Vypise aktualne blokovane uzivatele.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Counting blokovani", [
          "Prikaz ma vypsat kdo je blokovany a do kdy.",
          "Urcene pro counting kanal a perzistentni block store.",
          "Chybi dopojit data a vypocet zbyvajiciho casu.",
        ]);
      },
    },
    {
      name: "odblokuj",
      description: "Rucne odblokuje uzivatele v countingu.",
      adminOnly: true,
      configure: (builder) =>
        builder.addUserOption((option) =>
          option.setName("clen").setDescription("Clen k odblokovani").setRequired(true),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Counting odblokovani", [
          `Clen: ${interaction.options.getUser("clen", true)}`,
          "Po odblokovani ma prijit reset fail streaku.",
          "Chybi dopojit counting persistence.",
        ]);
      },
    },
    {
      name: "nastav-kanal",
      description: "Pripravi prepnuti counting kanalu.",
      adminOnly: true,
      configure: (builder) =>
        builder.addChannelOption((option) =>
          option
            .setName("kanal")
            .setDescription("Novy counting kanal")
            .setRequired(true)
            .addChannelTypes(ChannelType.GuildText),
        ),
      execute: async (interaction, context) => {
        const channel = interaction.options.getChannel("kanal", true);
        await replyPlanned(interaction, context, "Counting kanal", [
          `Novy kanal: ${channel}`,
          "Slash command ma zapsat channel ID do konfigurace.",
          "Chybi bezpecna persist vrstva pro config update bez restartu.",
        ]);
      },
    },
    {
      name: "kanal",
      description: "Ukaze aktualni counting kanal.",
      adminOnly: true,
      execute: async (interaction, context) => {
        const embed = createBaseEmbed(
          context,
          "Counting kanal",
          `Aktualni counting kanal: ${context.services.counting.getChannelMention()}`,
        );
        await replyWithEmbed(interaction, embed, true);
      },
    },
    {
      name: "pravidla",
      description: "Vypise pravidla countingu.",
      execute: async (interaction, context) => {
        const embed = createBaseEmbed(
          context,
          "Pravidla countingu",
          context.services.counting.getRules().map((line, index) => `${index + 1}. ${line}`).join("\n"),
        );
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "statistiky",
      description: "Vypise counting statistiky.",
      configure: (builder) =>
        builder.addUserOption((option) =>
          option.setName("clen").setDescription("Volitelne jedna osoba").setRequired(false),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Counting statistiky", [
          `Zadany clen: ${interaction.options.getUser("clen") ?? "zadny, top 10"}`,
          "Prikaz ma umet top 10 i detail jedne osoby.",
          "Chybi counting stats store.",
        ], false);
      },
    },
    {
      name: "formaty",
      description: "Ukaze podporovane formaty cisel.",
      execute: async (interaction, context) => {
        const embed = createBaseEmbed(
          context,
          "Podporovane formaty countingu",
          context.services.counting.getSupportedFormats().join("\n"),
        );
        await replyWithEmbed(interaction, embed);
      },
    },
  ],
});
