import { EmbedBuilder, type ChatInputCommandInteraction } from "discord.js";

import type { AppContext } from "../../../app/context.js";

export const createBaseEmbed = (
  context: AppContext,
  title: string,
  description?: string,
): EmbedBuilder => {
  const embed = new EmbedBuilder()
    .setColor(context.config.branding.embedColor)
    .setTitle(title)
    .setFooter({ text: context.config.branding.footerText })
    .setTimestamp();

  if (description) {
    embed.setDescription(description);
  }

  return embed;
};

export const replyWithEmbeds = async (
  interaction: ChatInputCommandInteraction,
  embeds: EmbedBuilder[],
  ephemeral = false,
) => {
  if (interaction.deferred || interaction.replied) {
    await interaction.followUp({ embeds, ephemeral });
    return;
  }

  await interaction.reply({ embeds, ephemeral });
};

export const replyWithEmbed = async (
  interaction: ChatInputCommandInteraction,
  embed: EmbedBuilder,
  ephemeral = false,
) => replyWithEmbeds(interaction, [embed], ephemeral);

export const replyPlanned = async (
  interaction: ChatInputCommandInteraction,
  context: AppContext,
  title: string,
  bullets: string[],
  ephemeral = true,
) => {
  const embed = createBaseEmbed(
    context,
    title,
    "Slash command uz je pripraveny, ale domenova logika se jeste musi dopojit.",
  ).addFields({
    name: "Co je pripravene",
    value: bullets.map((bullet) => `- ${bullet}`).join("\n"),
  });

  await replyWithEmbed(interaction, embed, ephemeral);
};
