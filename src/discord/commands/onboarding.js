import { Colors, EmbedBuilder, MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly } from './helpers.js';

const fillDefaultRolesCommand = {
  meta: { category: 'onboarding', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('doplnit-default-roli')
      .setDescription('Projede všechny členy a doplní default roli.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const config = await context.configStore.get();
    if (!config.guild.defaultRoleId) {
      throw new Error('Defaultní role není nastavená v konfiguraci.');
    }

    const defaultRole = interaction.guild.roles.cache.get(config.guild.defaultRoleId)
      ?? await interaction.guild.roles.fetch(config.guild.defaultRoleId).catch(() => null);

    if (!defaultRole) {
      throw new Error(`Defaultní role s ID ${config.guild.defaultRoleId} nebyla nalezena.`);
    }

    const report = await context.services.welcome.backfillDefaultRole(interaction.guild);

    const embed = new EmbedBuilder()
      .setTitle('Kontrola rolí dokončena')
      .setDescription(`Role ${defaultRole} byla zkontrolována u všech uživatelů.`)
      .setColor(Colors.Green)
      .addFields({
        name: 'Statistiky',
        value: [
          `Celkem uživatelů: **${report.scanned}**`,
          `Přiděleno rolí: **${report.added}**`,
          `Přeskočeno botů: **${report.skippedBots}**`,
          `Chyby: **${report.failed}**`
        ].join('\n')
      })
      .setTimestamp(new Date());

    await interaction.editReply({
      content: null,
      embeds: [embed]
    });
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
  return [fillDefaultRolesCommand, reactionRoleSyncCommand];
}
