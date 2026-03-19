import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { guildOnly, sendChunksToDm } from './helpers.js';

const saveBookmarkCommand = {
  meta: { category: 'bookmarks', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('bookmark-uloz')
      .setDescription('Uloží bookmark podle odkazu na zprávu.')
      .addStringOption((option) =>
        option
          .setName('message-link')
          .setDescription('Discord odkaz na zprávu.')
          .setRequired(true)
      )
      .addStringOption((option) =>
        option
          .setName('poznamka')
          .setDescription('Volitelná poznámka.')
          .setRequired(false)
      )
  ),
  async execute(context, interaction) {
    await context.services.bookmarks.saveFromLink(
      interaction.user.id,
      interaction.options.getString('message-link', true),
      interaction.options.getString('poznamka'),
      interaction.guild
    );
    await interaction.reply({ content: 'Bookmark uložen.', flags: MessageFlags.Ephemeral });
  }
};

const listBookmarksCommand = {
  meta: { category: 'bookmarks', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('bookmarky')
      .setDescription('Pošle tvoje bookmarky do DM.')
      .addIntegerOption((option) =>
        option
          .setName('strana')
          .setDescription('Číslo strany.')
          .setRequired(false)
          .setMinValue(1)
      )
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const page = interaction.options.getInteger('strana') ?? 1;
    const result = await context.services.bookmarks.list(interaction.user.id, page);
    const text = result.items.length
      ? result.items.map((item, index) => `${index + 1}. [zpráva](${item.jump_url})${item.note ? ` - ${item.note}` : ''}`).join('\n')
      : 'Na téhle straně nic není.';
    await sendChunksToDm(interaction.user, `Bookmarky ${result.page}/${result.totalPages}`, text);
    await interaction.editReply('Bookmarky jsem poslal do DM.');
  }
};

const deleteBookmarkCommand = {
  meta: { category: 'bookmarks', adminOnly: false, hidden: false },
  data: guildOnly(
    new SlashCommandBuilder()
      .setName('bookmark-smaz')
      .setDescription('Smaže bookmark podle pořadí.')
      .addIntegerOption((option) =>
        option
          .setName('index')
          .setDescription('Pořadové číslo bookmarku.')
          .setRequired(true)
          .setMinValue(1)
      )
  ),
  async execute(context, interaction) {
    await context.services.bookmarks.delete(interaction.user.id, interaction.options.getInteger('index', true));
    await interaction.reply({ content: 'Bookmark smazán.', flags: MessageFlags.Ephemeral });
  }
};

export function getBookmarkCommands() {
  return [saveBookmarkCommand, listBookmarksCommand, deleteBookmarkCommand];
}
