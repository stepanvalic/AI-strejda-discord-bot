import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly } from './helpers.js';

const timeoutCommand = {
  meta: { category: 'moderation', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('timeout')
      .setDescription('Udělí člověku timeout.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Koho timeoutnout.')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('delka')
          .setDescription('Například 5m, 2h nebo 1d12h.')
          .setRequired(false)
      )
      .addStringOption((option) =>
        option
          .setName('duvod')
          .setDescription('Volitelný důvod.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const member = await interaction.guild.members.fetch(interaction.options.getUser('clen').id);
    const embed = await context.services.moderation.timeout(
      member,
      interaction.options.getString('delka'),
      interaction.options.getString('duvod'),
      interaction.user
    );
    await interaction.reply({ embeds: [embed] });
  }
};

const untimeoutCommand = {
  meta: { category: 'moderation', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('untimeout')
      .setDescription('Zruší timeout.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Koho odtimeoutnout.')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('duvod')
          .setDescription('Volitelný důvod.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const member = await interaction.guild.members.fetch(interaction.options.getUser('clen').id);
    const embed = await context.services.moderation.untimeout(
      member,
      interaction.options.getString('duvod'),
      interaction.user
    );
    await interaction.reply({ embeds: [embed] });
  }
};

const banCommand = {
  meta: { category: 'moderation', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('ban')
      .setDescription('Dá člověku ban.')
      .addUserOption((option) =>
        option
          .setName('clen')
          .setDescription('Koho zabanovat.')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('duvod')
          .setDescription('Volitelný důvod.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const member = await interaction.guild.members.fetch(interaction.options.getUser('clen').id);
    const embed = await context.services.moderation.ban(
      member,
      interaction.options.getString('duvod'),
      interaction.user
    );
    await interaction.reply({ embeds: [embed] });
  }
};

const unbanCommand = {
  meta: { category: 'moderation', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('unban')
      .setDescription('Odbanuje uživatele podle ID.')
      .addStringOption((option) =>
        option
          .setName('user-id')
          .setDescription('Discord user ID.')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('duvod')
          .setDescription('Volitelný důvod.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    const embed = await context.services.moderation.unban(
      interaction.guild,
      interaction.options.getString('user-id'),
      interaction.options.getString('duvod'),
      interaction.user
    );
    await interaction.reply({ embeds: [embed] });
  }
};

export function getModerationCommands() {
  return [timeoutCommand, untimeoutCommand, banCommand, unbanCommand];
}
