import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly, ensureTextChannelOption, guildOnly } from './helpers.js';

const uptimeCommand = {
  meta: { category: 'utility', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('uptime')
      .setDescription('Ukáže, jak dlouho bot běží.')
  ),
  async execute(context, interaction) {
    await interaction.reply(await context.services.utility.getUptimeResponse());
  }
};

const inviteCommand = {
  meta: { category: 'utility', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('pozvanka')
      .setDescription('Vytvoří permanentní invite.')
  ),
  async execute(context, interaction) {
    await interaction.reply(await context.services.utility.createInvite(interaction));
  }
};

const commandsCommand = {
  meta: { category: 'utility', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('prikazy')
      .setDescription('Ukáže kompletní seznam slash commandů.')
  ),
  async execute(context, interaction) {
    const includeAdmin = interaction.memberPermissions?.has('Administrator') ?? false;
    await interaction.reply(await context.services.utility.getCommandListResponse(context.commands, includeAdmin));
  }
};

const helpCommand = {
  meta: { category: 'utility', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('help')
      .setDescription('Ukáže příkazy pro běžné uživatele.')
  ),
  async execute(context, interaction) {
    await interaction.reply(await context.services.utility.getCommandListResponse(context.commands, false));
  }
};

const rulesCommand = {
  meta: { category: 'utility', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('pravidla')
      .setDescription('Ukáže serverová pravidla.')
  ),
  async execute(context, interaction) {
    await interaction.reply(await context.services.utility.getRulesResponse());
  }
};

const publishRulesCommand = {
  meta: { category: 'utility', adminOnly: true, hidden: false },
  data: ensureTextChannelOption(
    adminOnly(
      new SlashCommandBuilder()
        .setName('pravidla-publikovat')
        .setDescription('Pošle nebo aktualizuje embed s pravidly.')
        .addStringOption((option) =>
          option
            .setName('message-id')
            .setDescription('Pokud chceš upravit existující zprávu.')
            .setRequired(false)
        )
    ),
    'kanal',
    'Kanál pro odeslání pravidel.',
    false
  ),
  async execute(context, interaction) {
    const channel = interaction.options.getChannel('kanal');
    const messageId = interaction.options.getString('message-id');
    const message = await context.services.utility.publishRules(channel?.id, messageId);
    await interaction.reply({
      content: `Pravidla hotová: ${message.url ?? 'zpráva upravena'}`,
      flags: MessageFlags.Ephemeral
    });
  }
};

export function getUtilityCommands() {
  return [
    uptimeCommand,
    inviteCommand,
    commandsCommand,
    helpCommand,
    rulesCommand,
    publishRulesCommand
  ];
}
