import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly, guildOnly } from './helpers.js';

const rewelcomeCommand = {
  meta: { category: 'onboarding', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('uvitat')
      .setDescription('Znovu pustí welcome flow pro člena.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Volitelný člen, jinak ty.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const user = interaction.options.getUser('clen') ?? interaction.user;
    const member = await interaction.guild.members.fetch(user.id);
    const result = await context.services.welcome.rewelcome(member);
    await interaction.reply({
      content: `Welcome flow proběhl. Default role ${result.roleAdded ? 'doplněna' : 'beze změny'}.`,
      flags: MessageFlags.Ephemeral
    });
  }
};

const fillDefaultRolesCommand = {
  meta: { category: 'onboarding', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('doplnit-default-roli')
      .setDescription('Projede všechny členy a doplní default roli.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const report = await context.services.welcome.backfillDefaultRole(interaction.guild);
    await interaction.editReply(
      `Proskenováno: ${report.scanned}, přidáno: ${report.added}, botů přeskočeno: ${report.skippedBots}, failů: ${report.failed}.`
    );
  }
};

const reactionRoleSyncCommand = {
  meta: { category: 'onboarding', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('reaction-roles-sync')
      .setDescription('Znovu vytvoří nebo upraví reaction role zprávu.')
  ),
  async execute(context, interaction) {
    const message = await context.services.reactionRoles.syncMessage(interaction.guild);
    await interaction.reply({
      content: `Reaction role panel je hotový: ${message.url}`,
      flags: MessageFlags.Ephemeral
    });
  }
};

export function getOnboardingCommands() {
  return [rewelcomeCommand, fillDefaultRolesCommand, reactionRoleSyncCommand];
}
