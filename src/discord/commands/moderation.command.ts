import { formatDuration } from "../../shared/time/format-duration.js";
import { createGroupCommand } from "./support/group-command.js";
import { createBaseEmbed, replyPlanned, replyWithEmbed } from "./support/response.js";

export const moderationCommand = createGroupCommand({
  name: "moderation",
  description: "Moderacni slash commandy.",
  category: "Moderation",
  subcommands: [
    {
      name: "timeout",
      description: "Udeli timeout clenu.",
      adminOnly: true,
      configure: (builder) =>
        builder
          .addUserOption((option) =>
            option.setName("clen").setDescription("Clen pro timeout").setRequired(true),
          )
          .addStringOption((option) =>
            option
              .setName("delka")
              .setDescription("Napriklad 15m, 2h nebo 1d12h")
              .setRequired(false),
          )
          .addStringOption((option) =>
            option.setName("duvod").setDescription("Duvod timeoutu").setRequired(false),
          ),
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Timeout selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const user = interaction.options.getUser("clen", true);
        const member = await interaction.guild.members.fetch(user.id).catch(() => null);
        if (!member) {
          const embed = createBaseEmbed(context, "Timeout selhal", "Zadany clen nebyl nalezen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const duration = await context.services.moderation.timeout(
          member,
          interaction.options.getString("delka") ?? undefined,
          interaction.options.getString("duvod") ?? undefined,
        );

        const embed = createBaseEmbed(
          context,
          "Timeout udelen",
          `${member} dostal timeout na ${formatDuration(duration)}.`,
        );
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "untimeout",
      description: "Zrusi timeout clena.",
      adminOnly: true,
      configure: (builder) =>
        builder
          .addUserOption((option) =>
            option.setName("clen").setDescription("Clen pro zruseni timeoutu").setRequired(true),
          )
          .addStringOption((option) =>
            option.setName("duvod").setDescription("Duvod zruseni").setRequired(false),
          ),
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Untimeout selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const user = interaction.options.getUser("clen", true);
        const member = await interaction.guild.members.fetch(user.id).catch(() => null);
        if (!member) {
          const embed = createBaseEmbed(context, "Untimeout selhal", "Zadany clen nebyl nalezen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await context.services.moderation.untimeout(
          member,
          interaction.options.getString("duvod") ?? undefined,
        );

        const embed = createBaseEmbed(context, "Timeout zrusen", `${member} uz nema timeout.`);
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "ban",
      description: "Zabanuje clena.",
      adminOnly: true,
      configure: (builder) =>
        builder
          .addUserOption((option) =>
            option.setName("clen").setDescription("Clen pro ban").setRequired(true),
          )
          .addStringOption((option) =>
            option.setName("duvod").setDescription("Duvod banu").setRequired(false),
          ),
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Ban selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const user = interaction.options.getUser("clen", true);
        const member = await interaction.guild.members.fetch(user.id).catch(() => null);
        if (!member) {
          const embed = createBaseEmbed(context, "Ban selhal", "Zadany clen nebyl nalezen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await context.services.moderation.ban(
          member,
          interaction.options.getString("duvod") ?? undefined,
        );

        const embed = createBaseEmbed(context, "Ban udelen", `${member.user.tag} byl zabanovan.`);
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "unban",
      description: "Provadi unban podle user ID.",
      adminOnly: true,
      configure: (builder) =>
        builder
          .addStringOption((option) =>
            option
              .setName("user-id")
              .setDescription("Discord user ID")
              .setRequired(true),
          )
          .addStringOption((option) =>
            option.setName("duvod").setDescription("Duvod unbanu").setRequired(false),
          ),
      execute: async (interaction, context) => {
        if (!interaction.guild) {
          const embed = createBaseEmbed(context, "Unban selhal", "Tenhle command funguje jen na serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const userId = interaction.options.getString("user-id", true);
        await context.services.moderation.unban(
          interaction.guild,
          userId,
          interaction.options.getString("duvod") ?? undefined,
        );

        const embed = createBaseEmbed(context, "Unban hotovy", `Uzivatel \`${userId}\` byl odbanovan.`);
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "blacklist-pridej",
      description: "Prida slovo do word filtru.",
      adminOnly: true,
      configure: (builder) =>
        builder.addStringOption((option) =>
          option.setName("slovo").setDescription("Zakazane slovo").setRequired(true),
        ),
      execute: async (interaction, context) => {
        const word = interaction.options.getString("slovo", true);
        const auditChannelId = context.config.channels.auditLogChannelId;

        if (auditChannelId && interaction.channelId !== auditChannelId) {
          const embed = createBaseEmbed(
            context,
            "Word filter sprava",
            `Tenhle slash command ma bezet v <#${auditChannelId}>.`,
          );
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await replyPlanned(interaction, context, "Blacklist slovo", [
          `Pozadovane slovo: ${word}`,
          "Slash rozhrani je pripravene pro admin-only flow.",
          "Chybi dopsat ulozeni do blacklist store a audit zaznam.",
        ]);
      },
    },
  ],
});
