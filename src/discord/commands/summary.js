import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly, ensureTextChannelOption, guildOnly, parseSummaryDateInput } from './helpers.js';
import { getYesterdayDateString } from '../../shared/utils.js';

const dailySummaryCommand = {
  meta: { category: 'summary', adminOnly: true, hidden: false },
  data: ensureTextChannelOption(
    adminOnly(
      new SlashCommandBuilder()
      .setName('summary-den')
      .setDescription('Vygeneruje denní shrnutí pro zvolený den.')
        .addStringOption((option) =>
          option
            .setName('datum')
            .setDescription('DD/MM/YYYY nebo YYYY-MM-DD, jinak včera.')
            .setRequired(false)
        )
        .addBooleanOption((option) =>
          option
            .setName('force')
            .setDescription('Přepiš existující summary.')
            .setRequired(false)
        )
    ),
    'kanal',
    'Volitelný cílový kanál.',
    false
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const date = parseSummaryDateInput(
      interaction.options.getString('datum'),
      getYesterdayDateString(context.env.TIMEZONE)
    );
    const summary = await context.services.summary.generateDailySummary(date, {
      requestedBy: interaction.user.id,
      manual: true,
      force: interaction.options.getBoolean('force') ?? false
    });
    const channel = interaction.options.getChannel('kanal');
    await context.services.summary.sendSummaryToChannel(interaction.guild, summary, channel?.id);
    await interaction.editReply(`Summary pro ${date} je hotové.`);
  }
};

const recentSummaryCommand = {
  meta: { category: 'summary', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('summary-posledni')
      .setDescription('Pošle DM shrnutí posledních N zpráv.')
      .addIntegerOption((option) =>
        option
          .setName('pocet')
          .setDescription('10 až 500.')
          .setRequired(true)
          .setMinValue(10)
          .setMaxValue(500)
      )
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const count = interaction.options.getInteger('pocet', true);
    const result = await context.services.summary.summarizeRecentForUser(interaction.member, count);
    await context.services.summary.sendSummaryToUserDm(interaction.user, result);
    await interaction.editReply('Shrnutí jsem poslal do DM.');
  }
};

const todayCountCommand = {
  meta: { category: 'summary', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('summary-pocet-dnes')
      .setDescription('Vrátí počet dnes uložených zpráv ve summary store.')
  ),
  async execute(context, interaction) {
    const count = await context.services.summary.getTodayMessageCount();
    await interaction.reply({ content: `Dnes je uloženo ${count} zpráv.`, flags: MessageFlags.Ephemeral });
  }
};

export function getSummaryCommands() {
  return [dailySummaryCommand, recentSummaryCommand, todayCountCommand];
}
