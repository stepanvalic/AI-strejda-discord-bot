import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly, ensureTextChannelOption } from './helpers.js';
import { chunkText } from '../../shared/utils.js';

async function replyWithChunks(interaction, text) {
  const chunks = chunkText(text, 1800);

  await interaction.reply({
    content: chunks[0],
    flags: MessageFlags.Ephemeral
  });

  for (const chunk of chunks.slice(1)) {
    await interaction.followUp({
      content: chunk,
      flags: MessageFlags.Ephemeral
    });
  }
}

const moderationStatusCommand = {
  meta: { category: 'moderation', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('moderace-stav')
      .setDescription('Ukáže stav archivu zpráv pro moderaci.')
  ),
  async execute(context, interaction) {
    const stats = await context.services.moderation.getArchiveStats();
    const latest = stats.latestMessage
      ? `${stats.latestMessage.created_at} v #${stats.latestMessage.channel_name || 'neznámý-kanál'}`
      : 'zatím nic';

    await interaction.reply({
      content: [
        'Archiv moderace:',
        `Celkem zpráv: ${stats.totalMessages}`,
        `Dnes uložených: ${stats.archivedToday}`,
        `Unikátních uživatelů: ${stats.uniqueUsers}`,
        `Kanálů: ${stats.uniqueChannels}`,
        `Poslední uložená zpráva: ${latest}`
      ].join('\n'),
      flags: MessageFlags.Ephemeral
    });
  }
};

const moderationRecentCommand = {
  meta: { category: 'moderation', adminOnly: true, hidden: false },
  data: ensureTextChannelOption(
    adminOnly(
      new SlashCommandBuilder()
        .setName('moderace-posledni')
        .setDescription('Vrátí poslední zprávy z moderačního archivu.')
        .addIntegerOption((option) =>
          option
            .setName('pocet')
            .setDescription('Kolik zpráv chceš vypsat.')
            .setRequired(false)
            .setMinValue(1)
            .setMaxValue(20)
        )
    ),
    'kanal',
    'Volitelně filtruj podle kanálu.',
    false
  ),
  async execute(context, interaction) {
    const count = interaction.options.getInteger('pocet') ?? 10;
    const channel = interaction.options.getChannel('kanal');
    const messages = await context.services.moderation.findMessages({
      limit: count,
      channelId: channel?.id || null
    });

    await replyWithChunks(
      interaction,
      context.services.moderation.formatMessageList(messages)
    );
  }
};

const moderationSearchCommand = {
  meta: { category: 'moderation', adminOnly: true, hidden: false },
  data: ensureTextChannelOption(
    adminOnly(
      new SlashCommandBuilder()
        .setName('moderace-hledat')
        .setDescription('Hledá text v archivu zpráv.')
        .addStringOption((option) =>
          option
            .setName('text')
            .setDescription('Hledaný text.')
            .setRequired(true)
        )
        .addIntegerOption((option) =>
          option
            .setName('pocet')
            .setDescription('Maximální počet výsledků.')
            .setRequired(false)
            .setMinValue(1)
            .setMaxValue(20)
        )
    ),
    'kanal',
    'Volitelně filtruj podle kanálu.',
    false
  ),
  async execute(context, interaction) {
    const query = interaction.options.getString('text', true);
    const count = interaction.options.getInteger('pocet') ?? 10;
    const channel = interaction.options.getChannel('kanal');
    const messages = await context.services.moderation.findMessages({
      limit: count,
      query,
      channelId: channel?.id || null
    });

    await replyWithChunks(
      interaction,
      `Výsledky pro "${query}":\n${context.services.moderation.formatMessageList(messages)}`
    );
  }
};

export function getModerationCommands() {
  return [moderationStatusCommand, moderationRecentCommand, moderationSearchCommand];
}
