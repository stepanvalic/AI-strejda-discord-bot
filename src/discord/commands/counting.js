import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly, ensureTextChannelOption, guildOnly } from './helpers.js';

function assertCountingChannel(context, interaction) {
  const channelId = interaction.channelId;
  return context.configStore.get().then((config) => {
    if (channelId !== config.counting.channelId) {
      throw new Error('Tenhle command funguje jen v counting kanálu.');
    }
  });
}

const statusCommand = {
  meta: { category: 'counting', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('counting-stav')
      .setDescription('Ukáže aktuální stav countingu.')
  ),
  async execute(context, interaction) {
    await assertCountingChannel(context, interaction);
    const status = await context.services.counting.getStatus();
    await interaction.reply({
      content: `Aktuálně: ${status.current}, další: ${status.expected}, rekord: ${status.highScore}, failů: ${status.failedCounts}.`,
      flags: MessageFlags.Ephemeral
    });
  }
};

const resetCommand = {
  meta: { category: 'counting', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('counting-reset')
      .setDescription('Resetuje counting na nulu.')
  ),
  async execute(context, interaction) {
    await assertCountingChannel(context, interaction);
    await context.services.counting.reset();
    await interaction.reply({ content: 'Counting resetován.', flags: MessageFlags.Ephemeral });
  }
};

const blockCommand = {
  meta: { category: 'counting', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('counting-block')
      .setDescription('Ručně zablokuje uživatele v countingu.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Koho bloknout.')
          .setRequired(true)
      )
      .addIntegerOption((option) =>
        option
          .setName('dny')
          .setDescription('Na kolik dní.')
          .setRequired(true)
          .setMinValue(1)
      )
  ),
  async execute(context, interaction) {
    await assertCountingChannel(context, interaction);
    const member = await interaction.guild.members.fetch(interaction.options.getUser('clen').id);
    await context.services.counting.blockUser(member, interaction.options.getInteger('dny'));
    await interaction.reply({ content: `${member} je bloknutý.`, flags: MessageFlags.Ephemeral });
  }
};

const blockListCommand = {
  meta: { category: 'counting', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('counting-blocklist')
      .setDescription('Ukáže blokované uživatele.')
  ),
  async execute(context, interaction) {
    await assertCountingChannel(context, interaction);
    const blocked = await context.services.counting.listBlocked();
    await interaction.reply({
      content: blocked.length
        ? blocked.map((entry) => `<@${entry.userId}> do ${entry.end_time} (${entry.duration_days} dny)`).join('\n')
        : 'Nikdo blokovaný není.',
      flags: MessageFlags.Ephemeral
    });
  }
};

const unblockCommand = {
  meta: { category: 'counting', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('counting-unblock')
      .setDescription('Ručně odblokuje uživatele.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Koho odblokovat.')
          .setRequired(true)
      )
  ),
  async execute(context, interaction) {
    await assertCountingChannel(context, interaction);
    const user = interaction.options.getUser('clen');
    await context.services.counting.unblockUser(user.id);
    await interaction.reply({ content: `${user} odblokován.`, flags: MessageFlags.Ephemeral });
  }
};

const setChannelCommand = {
  meta: { category: 'counting', adminOnly: true, hidden: false },
  data: ensureTextChannelOption(
    adminOnly(
      new SlashCommandBuilder()
        .setName('counting-kanal-nastav')
        .setDescription('Přepíše counting kanál v configu.')
    ),
    'kanal',
    'Nový counting kanál.',
    true
  ),
  async execute(context, interaction) {
    const channel = interaction.options.getChannel('kanal', true);
    await context.services.counting.setChannel(channel.id);
    await interaction.reply({ content: `Counting kanál nastaven na ${channel}.`, flags: MessageFlags.Ephemeral });
  }
};

const showChannelCommand = {
  meta: { category: 'counting', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('counting-kanal')
      .setDescription('Ukáže aktuální counting kanál.')
  ),
  async execute(context, interaction) {
    const config = await context.configStore.get();
    await interaction.reply({ content: `Counting kanál: <#${config.counting.channelId}>`, flags: MessageFlags.Ephemeral });
  }
};

const rulesCommand = {
  meta: { category: 'counting', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('counting-pravidla')
      .setDescription('Ukáže pravidla countingu.')
  ),
  async execute(context, interaction) {
    await interaction.reply({ content: context.services.counting.getRulesText() });
  }
};

const statsCommand = {
  meta: { category: 'counting', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('counting-statistiky')
      .setDescription('Top 10 nebo detail pro jednoho uživatele.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Volitelný člen.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const user = interaction.options.getUser('clen');
    const stats = await context.services.counting.getStats(user?.id);
    const content = user
      ? (stats
          ? `${user}: correct ${stats.correct_counts}, wrong ${stats.wrong_counts}, accuracy ${stats.correct_counts + stats.wrong_counts ? Math.round((stats.correct_counts / (stats.correct_counts + stats.wrong_counts)) * 100) : 0}%`
          : 'Tenhle uživatel zatím nemá counting statistiky.')
      : stats.map((entry, index) => `${index + 1}. <@${entry.userId}> - ${entry.correct_counts}`).join('\n');
    await interaction.reply({ content });
  }
};

const formatsCommand = {
  meta: { category: 'counting', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('counting-formaty')
      .setDescription('Ukáže podporované formáty čísel.')
  ),
  async execute(context, interaction) {
    await interaction.reply({ content: context.services.counting.getFormatsText() });
  }
};

export function getCountingCommands() {
  return [
    statusCommand,
    resetCommand,
    blockCommand,
    blockListCommand,
    unblockCommand,
    setChannelCommand,
    showChannelCommand,
    rulesCommand,
    statsCommand,
    formatsCommand
  ];
}
