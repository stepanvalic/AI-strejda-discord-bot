import { createGroupCommand } from "./support/group-command.js";
import { createBaseEmbed, replyPlanned, replyWithEmbed } from "./support/response.js";

export const onboardingCommand = createGroupCommand({
  name: "onboarding",
  description: "Welcome flow a udrzba roli.",
  category: "Onboarding",
  subcommands: [
    {
      name: "privitat",
      description: "Rucne znovu spusti welcome flow.",
      adminOnly: true,
      configure: (builder) =>
        builder.addUserOption((option) =>
          option.setName("clen").setDescription("Clen pro znovuprivitani").setRequired(false),
        ),
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Welcome selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const targetUser = interaction.options.getUser("clen") ?? interaction.user;
        const targetMember = await interaction.guild.members.fetch(targetUser.id);
        const result = await context.services.welcome.sendWelcome(targetMember);

        const embed = createBaseEmbed(
          context,
          "Welcome flow hotovy",
          [
            `Clen: ${targetMember}`,
            `Default role: ${result.roleAssigned ? "doplnena" : "beze zmeny"}`,
            `Welcome zprava: ${result.messageSent ? "odeslana" : "kanal chybi"}`,
          ].join("\n"),
        );
        await replyWithEmbed(interaction, embed, true);
      },
    },
    {
      name: "doplnit-default-role",
      description: "Doplni vychozi roli vsem clenym bez role.",
      adminOnly: true,
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Role sync selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const result = await context.services.welcome.assignDefaultRoleToEveryone(interaction.guild);
        const embed = createBaseEmbed(
          context,
          "Default role sync",
          [
            `Proskenovano: ${result.scanned}`,
            `Doplneno: ${result.updated}`,
            `Preskoceni boti: ${result.skippedBots}`,
          ].join("\n"),
        );
        await replyWithEmbed(interaction, embed, true);
      },
    },
    {
      name: "sync-reaction-roles",
      description: "Pripravi sync reaction role zpravy z configu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Reaction role sync", [
          "Slash command uz existuje a je navazany na onboarding domenu.",
          ...context.services.reactionRoles.describeMappings(),
          "Chybi dopsat tvorbu nebo editaci centralni reaction role zpravy.",
        ]);
      },
    },
  ],
});
