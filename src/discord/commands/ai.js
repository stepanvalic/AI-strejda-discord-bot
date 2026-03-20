import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { createEmbed } from '../../shared/discord-helpers.js';
import { adminOnly, guildOnly } from './helpers.js';

const aiScoreCommand = {
  meta: { category: 'ai', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('ai-skore')
      .setDescription('Ukáže AI skóre pro tebe nebo jiného člena.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Volitelný člen.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const user = interaction.options.getUser('clen') ?? interaction.user;
    await interaction.deferReply();
    await interaction.editReply({
      embeds: [await context.services.ai.getUserScoreEmbed(user)]
    });
  }
};

const aiTopCommand = {
  meta: { category: 'ai', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('ai-top')
      .setDescription('Top 10 podle AI score.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply();
    await interaction.editReply({
      embeds: [await context.services.ai.getLeaderboardEmbed(interaction.guild, true)]
    });
  }
};

const aiBottomCommand = {
  meta: { category: 'ai', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('ai-bottom')
      .setDescription('Bottom 10 podle AI score.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply();
    await interaction.editReply({
      embeds: [await context.services.ai.getLeaderboardEmbed(interaction.guild, false)]
    });
  }
};

const aiSyncRolesCommand = {
  meta: { category: 'ai', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('ai-sync-role')
      .setDescription('Projede členy a opraví AI role.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const updated = await context.services.ai.syncAllRoles(interaction.guild);
    await interaction.editReply({
      embeds: [
        createEmbed({
          title: '✅ AI role sync hotov',
          description: `Prošlo členů: **${updated}**`,
          footer: 'AI moderační systém'
        })
      ]
    });
  }
};

const aiRulesCommand = {
  meta: { category: 'ai', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('ai-pravidla')
      .setDescription('Ukáže pravidla AI scoringu.')
  ),
  async execute(context, interaction) {
    const embed = await context.services.ai.getRulesEmbed();
    await interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
  }
};

export function getAiCommands() {
  return [
    aiScoreCommand,
    aiTopCommand,
    aiBottomCommand,
    aiSyncRolesCommand,
    aiRulesCommand
  ];
}
