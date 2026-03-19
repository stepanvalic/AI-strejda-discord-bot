import { MessageFlags, SlashCommandBuilder } from 'discord.js';
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
    const score = await context.services.ai.getUserScore(user.id);
    await interaction.reply({
      content: score
        ? [
            `${user}`,
            `Total: ${score.total_score}`,
            `Positive: ${score.positive_score}`,
            `Negative: ${score.negative_score}`,
            `Messages: ${score.messages_analyzed}`
          ].join('\n')
        : 'Tenhle uživatel zatím nemá AI skóre.'
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
    const users = await context.services.ai.getTopUsers(true);
    await interaction.reply({
      content: users.length
        ? users.map((entry, index) => `${index + 1}. <@${entry.userId}> - ${entry.total_score}`).join('\n')
        : 'Zatím tu nic není.'
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
    const users = await context.services.ai.getTopUsers(false);
    await interaction.reply({
      content: users.length
        ? users.map((entry, index) => `${index + 1}. <@${entry.userId}> - ${entry.total_score}`).join('\n')
        : 'Zatím tu nic není.'
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
    await interaction.editReply(`AI role sync hotov. Prošlo ${updated} členů.`);
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

const aiResetUserCommand = {
  meta: { category: 'ai', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('ai-reset-user')
      .setDescription('Resetuje AI skóre jednoho člena.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Koho resetnout.')
          .setRequired(true)
      )
  ),
  async execute(context, interaction) {
    const member = await interaction.guild.members.fetch(interaction.options.getUser('clen').id);
    await context.services.ai.resetUser(member);
    await interaction.reply({ content: `${member} má AI skóre resetované.`, flags: MessageFlags.Ephemeral });
  }
};

const aiResetAllCommand = {
  meta: { category: 'ai', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('ai-reset-all')
      .setDescription('Resetuje AI skóre všem.')
      .addBooleanOption((option) =>
        option
          .setName('potvrdit')
          .setDescription('Musí být true, jinak nic.')
          .setRequired(true)
      )
  ),
  async execute(context, interaction) {
    if (!interaction.options.getBoolean('potvrdit')) {
      throw new Error('Bez potvrzení to neresetnu.');
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    await context.services.ai.resetAll(interaction.guild);
    await interaction.editReply('AI skóre všech uživatelů resetováno.');
  }
};

export function getAiCommands() {
  return [
    aiScoreCommand,
    aiTopCommand,
    aiBottomCommand,
    aiSyncRolesCommand,
    aiRulesCommand,
    aiResetUserCommand,
    aiResetAllCommand
  ];
}
