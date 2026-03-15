import { createGroupCommand } from "./support/group-command.js";
import { createBaseEmbed, replyPlanned, replyWithEmbed } from "./support/response.js";

export const aiCommand = createGroupCommand({
  name: "ai",
  description: "AI scoring slash commandy a reputacni pravidla.",
  category: "AI scoring",
  subcommands: [
    {
      name: "score",
      description: "Ukaze AI score uzivatele.",
      configure: (builder) =>
        builder.addUserOption((option) =>
          option.setName("clen").setDescription("Volitelne jiny clen").setRequired(false),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "AI score", [
          `Cilovy clen: ${interaction.options.getUser("clen") ?? interaction.user}`,
          "Command ma vypisovat total, positive, negative a messages analyzed.",
          "Chybi score repository a role sync stav.",
        ], false);
      },
    },
    {
      name: "top",
      description: "Top 10 podle AI score.",
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "AI top 10", [
          "Slash command je pripraveny pro descending total score.",
          "Chybi dotaz do persistentniho score store.",
          "Pozdeji sem pujde i leaderboard embed.",
        ], false);
      },
    },
    {
      name: "bottom",
      description: "Bottom 10 podle AI score.",
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "AI bottom 10", [
          "Slash command je pripraveny pro ascending total score.",
          "Docs explicitne rika, ze to ma byt samostatny command.",
          "Chybi score store.",
        ], false);
      },
    },
    {
      name: "sync-role",
      description: "Hromadna kontrola AI roli v Discordu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "AI role sync", [
          "Prikaz ma projit vsechny cleny bez botu a adminu.",
          "Ma porovnat Discord role a perzistentni data.",
          "Chybi score data a role synchronizator.",
        ]);
      },
    },
    {
      name: "pravidla",
      description: "Ukaze pravidla AI systemu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        const embed = createBaseEmbed(
          context,
          "AI scoring pravidla",
          context.services.aiScoring.buildRulesLines().join("\n"),
        );
        await replyWithEmbed(interaction, embed, true);
      },
    },
    {
      name: "reset-user",
      description: "Resetuje AI score jednoho uzivatele.",
      adminOnly: true,
      configure: (builder) =>
        builder.addUserOption((option) =>
          option.setName("clen").setDescription("Clen pro reset score").setRequired(true),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "AI reset user", [
          `Clen: ${interaction.options.getUser("clen", true)}`,
          "Prikaz ma smazat score a odebrat souvisejici role.",
          "Chybi AI score store a role cleanup.",
        ]);
      },
    },
    {
      name: "reset-all",
      description: "Resetuje AI score vsech uzivatelu.",
      adminOnly: true,
      configure: (builder) =>
        builder.addBooleanOption((option) =>
          option
            .setName("potvrdit")
            .setDescription("Potvrzeni hromadneho resetu")
            .setRequired(true),
        ),
      execute: async (interaction, context) => {
        const confirmed = interaction.options.getBoolean("potvrdit", true);
        if (!confirmed) {
          const embed = createBaseEmbed(context, "AI reset vsech zrusen", "Bez potvrzeni se nic nedeje.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await replyPlanned(interaction, context, "AI reset vsech", [
          "Slash verze pouziva boolean potvrzeni misto reakci.",
          "Po dopojeni ma vycistit score store a odebrat vsechny AI role.",
          "Chybi repository a bulk role removal.",
        ]);
      },
    },
  ],
});
