import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly } from './helpers.js';

const shutdownCommand = {
  meta: { category: 'hidden', adminOnly: true, hidden: true },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('shutdown')
      .setDescription('Vypne proces bota.')
  ),
  async execute(context, interaction) {
    await interaction.reply({ content: 'Tak jo, zhasinam.', flags: MessageFlags.Ephemeral });
    setTimeout(() => {
      context.client.destroy();
      process.exit(0);
    }, 250);
  }
};

export function getHiddenCommands() {
  return [shutdownCommand];
}
