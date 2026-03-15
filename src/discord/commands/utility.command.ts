import { ChannelType, type TextChannel } from "discord.js";

import { createGroupCommand } from "./support/group-command.js";
import { hasAdminPermission } from "./support/permissions.js";
import { createBaseEmbed, replyWithEmbed, replyWithEmbeds } from "./support/response.js";

export const utilityCommand = createGroupCommand({
  name: "utility",
  description: "Utility slash commandy pro bezny provoz serveru.",
  category: "Utility",
  subcommands: [
    {
      name: "youtube",
      description: "Posle odkaz na sledovany YouTube kanal.",
      execute: async (interaction, context) => {
        const url = context.services.utility.getYoutubeChannelUrl();
        const embed = createBaseEmbed(
          context,
          "YouTube kanal",
          url ?? "YouTube kanal jeste neni nastaveny v configu.",
        );

        if (url) {
          embed.setURL(url);
        }

        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "youtube-notifikace",
      description: "Ukaze kanal pro YouTube notifikace.",
      execute: async (interaction, context) => {
        const embed = createBaseEmbed(
          context,
          "YouTube notifikace",
          `Aktualni notifikacni kanal: ${context.services.utility.getYoutubeNotificationChannelMention()}`,
        );
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "uptime",
      description: "Vypise uptime procesu.",
      execute: async (interaction, context) => {
        const embed = createBaseEmbed(
          context,
          "Uptime",
          `Bot bezi uz ${context.services.utility.getUptimeText()}.`,
        );
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "invite",
      description: "Vytvori permanentni Discord invite.",
      execute: async (interaction, context) => {
        if (
          !interaction.guild ||
          !interaction.channel ||
          interaction.channel.type !== ChannelType.GuildText
        ) {
          const embed = createBaseEmbed(context, "Invite selhal", "Tenhle command musi bezet v textovem kanalu serveru.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const inviteUrl = await context.services.utility.createInvite(
          interaction.guild,
          interaction.channel as TextChannel,
        );

        const embed = createBaseEmbed(context, "Invite vytvoren", inviteUrl);
        await replyWithEmbed(interaction, embed);
      },
    },
    {
      name: "commands",
      description: "Vypise kompletni seznam commandu podle opravneni.",
      execute: async (interaction, context) => {
        const embeds = context.services.utility.buildCatalogEmbeds(
          context.commands.flatMap((command) => command.helpEntries),
          hasAdminPermission(interaction),
        );

        await replyWithEmbeds(
          interaction,
          embeds.length > 0 ? embeds : [createBaseEmbed(context, "Commandy", "Zatim neni co vypsat.")],
          true,
        );
      },
    },
    {
      name: "help",
      description: "Vypise commandy dostupne beznym uzivatelum.",
      execute: async (interaction, context) => {
        const embeds = context.services.utility.buildCatalogEmbeds(
          context.commands.flatMap((command) => command.helpEntries),
          false,
        );

        await replyWithEmbeds(
          interaction,
          embeds.length > 0 ? embeds : [createBaseEmbed(context, "Help", "Zatim neni co vypsat.")],
          true,
        );
      },
    },
    {
      name: "pravidla",
      description: "Posle nebo aktualizuje embed se serverovymi pravidly.",
      adminOnly: true,
      configure: (builder) =>
        builder
          .addChannelOption((option) =>
            option
              .setName("kanal")
              .setDescription("Cilovy kanal pro pravidla")
              .addChannelTypes(ChannelType.GuildText)
              .setRequired(false),
          )
          .addStringOption((option) =>
            option
              .setName("message-id")
              .setDescription("Pokud chces upravit existujici zpravu")
              .setRequired(false),
          ),
      execute: async (interaction, context) => {
        const targetChannel =
          interaction.options.getChannel("kanal") ??
          (interaction.channel?.isTextBased() ? interaction.channel : null);

        if (!targetChannel || !targetChannel.isTextBased()) {
          const embed = createBaseEmbed(context, "Pravidla selhala", "Nepodarilo se urcit cilovy textovy kanal.");
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        const rulesEmbed = context.services.utility.buildRulesEmbed();
        const messageId = interaction.options.getString("message-id");

        if (messageId && "messages" in targetChannel) {
          const message = await targetChannel.messages.fetch(messageId).catch(() => null);
          if (!message) {
            const embed = createBaseEmbed(context, "Pravidla selhala", `Zprava \`${messageId}\` nebyla v kanalu nalezena.`);
            await replyWithEmbed(interaction, embed, true);
            return;
          }

          await message.edit({ embeds: [rulesEmbed] });
          const embed = createBaseEmbed(context, "Pravidla upravena", `Embed byl upraven v ${targetChannel}.`);
          await replyWithEmbed(interaction, embed, true);
          return;
        }

        await targetChannel.send({ embeds: [rulesEmbed] });
        const embed = createBaseEmbed(context, "Pravidla odeslana", `Embed byl odeslan do ${targetChannel}.`);
        await replyWithEmbed(interaction, embed, true);
      },
    },
  ],
});
