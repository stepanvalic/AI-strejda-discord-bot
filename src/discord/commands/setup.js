import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly, ensureTextChannelOption } from './helpers.js';

const setupYoutubeChannelCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('setup-youtube-kanal')
      .setDescription('Vytvoří YouTube notifikační kanál.')
      .addStringOption((option) =>
        option
          .setName('nazev')
          .setDescription('Volitelný název kanálu.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const channel = await context.services.setup.createManagedChannel(
      interaction.guild,
      'youtube',
      interaction.options.getString('nazev')
    );
    await interaction.reply({ content: `Vytvořen kanál ${channel}.`, flags: MessageFlags.Ephemeral });
  }
};

const setupCountingChannelCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('setup-counting-kanal')
      .setDescription('Vytvoří counting kanál.')
      .addStringOption((option) =>
        option
          .setName('nazev')
          .setDescription('Volitelný název kanálu.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const channel = await context.services.setup.createManagedChannel(
      interaction.guild,
      'counting',
      interaction.options.getString('nazev')
    );
    await interaction.reply({ content: `Vytvořen kanál ${channel}.`, flags: MessageFlags.Ephemeral });
  }
};

const setupSummaryChannelCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('setup-summary-kanal')
      .setDescription('Vytvoří summary kanál.')
      .addStringOption((option) =>
        option
          .setName('nazev')
          .setDescription('Volitelný název kanálu.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const channel = await context.services.setup.createManagedChannel(
      interaction.guild,
      'summary',
      interaction.options.getString('nazev')
    );
    await interaction.reply({ content: `Vytvořen kanál ${channel}.`, flags: MessageFlags.Ephemeral });
  }
};

const setupAuditChannelCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('setup-audit-kanal')
      .setDescription('Vytvoří audit kanál.')
      .addStringOption((option) =>
        option
          .setName('nazev')
          .setDescription('Volitelný název kanálu.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const channel = await context.services.setup.createManagedChannel(
      interaction.guild,
      'audit',
      interaction.options.getString('nazev')
    );
    await interaction.reply({ content: `Vytvořen kanál ${channel}.`, flags: MessageFlags.Ephemeral });
  }
};

const setupAllCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('setup-vse')
      .setDescription('Vytvoří základní kanály a nastaví práva.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    await context.services.setup.createManagedChannel(interaction.guild, 'youtube');
    await context.services.setup.createManagedChannel(interaction.guild, 'counting');
    await context.services.setup.createManagedChannel(interaction.guild, 'summary');
    await context.services.setup.createManagedChannel(interaction.guild, 'audit');
    await context.services.setup.applyBasePermissions(interaction.guild);
    await interaction.editReply('Základní setup hotov.');
  }
};

const setupPermissionsCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('setup-prava')
      .setDescription('Nastaví práva základních kanálů.')
  ),
  async execute(context, interaction) {
    await context.services.setup.applyBasePermissions(interaction.guild);
    await interaction.reply({ content: 'Práva nastavena.', flags: MessageFlags.Ephemeral });
  }
};

const setupAuditExistingCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: ensureTextChannelOption(
    adminOnly(
      new SlashCommandBuilder()
        .setName('setup-audit-existujici')
        .setDescription('Použije existující kanál jako audit.')
    ),
    'kanal',
    'Cílový audit kanál.',
    true
  ),
  async execute(context, interaction) {
    const channel = interaction.options.getChannel('kanal', true);
    await context.services.setup.setAuditChannel(channel.id);
    await interaction.reply({ content: `Audit kanál nastaven na ${channel}.`, flags: MessageFlags.Ephemeral });
  }
};

const logLevelCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('log-level')
      .setDescription('Změní log level za běhu.')
      .addStringOption((option) =>
        option
          .setName('uroven')
          .setDescription('Nová úroveň logování.')
          .setRequired(true)
          .addChoices(
            { name: 'trace', value: 'trace' },
            { name: 'debug', value: 'debug' },
            { name: 'info', value: 'info' },
            { name: 'warn', value: 'warn' },
            { name: 'error', value: 'error' },
            { name: 'fatal', value: 'fatal' }
          )
      )
  ),
  async execute(context, interaction) {
    const level = interaction.options.getString('uroven', true);
    context.services.setup.changeLogLevel(level);
    await interaction.reply({ content: `Log level je ted ${level}.`, flags: MessageFlags.Ephemeral });
  }
};

const addFilteredWordCommand = {
  meta: { category: 'setup', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('filter-pridej-slovo')
      .setDescription('Přidá slovo do blacklistu.')
      .addStringOption((option) =>
        option
          .setName('slovo')
          .setDescription('Zakázané slovo.')
          .setRequired(true)
      )
  ),
  async execute(context, interaction) {
    const result = await context.services.wordFilter.addWord(
      interaction.options.getString('slovo', true),
      interaction.channelId
    );
    await interaction.reply({
      content: result.added ? `Přidáno slovo \`${result.word}\`.` : result.reason,
      flags: MessageFlags.Ephemeral
    });
  }
};

export function getSetupCommands() {
  return [
    setupYoutubeChannelCommand,
    setupCountingChannelCommand,
    setupSummaryChannelCommand,
    setupAllCommand,
    setupAuditChannelCommand,
    setupPermissionsCommand,
    setupAuditExistingCommand,
    logLevelCommand,
    addFilteredWordCommand
  ];
}
