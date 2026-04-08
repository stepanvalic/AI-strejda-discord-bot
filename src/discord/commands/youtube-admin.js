import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { adminOnly } from './helpers.js';

const youtubeCheckCommand = {
  meta: { category: 'youtube', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('youtube-check')
      .setDescription('Stáhne a případně oznámí nejnovější video.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const result = await context.services.youtube.checkLatestAndAnnounce();

    if (result.announced_count > 0) {
      await interaction.editReply(`Zkontrolováno. Oznámil jsem ${result.announced_count} videí. Poslední zpracované je ${result.video_id}.`);
      return;
    }

    await interaction.editReply(`Zkontrolováno. Nic nového k oznámení, poslední video je ${result.latest_video_id}.`);
  }
};

const youtubeRefreshCommand = {
  meta: { category: 'youtube', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('youtube-refresh')
      .setDescription('Aktualizuje metadata posledních oznámených videí.')
  ),
  async execute(context, interaction) {
    const updated = await context.services.youtube.refreshAnnouncements();
    await interaction.reply({ content: `Refresh hotov. Sáhlo se na ${updated} záznamů.`, flags: MessageFlags.Ephemeral });
  }
};

const youtubeResendCommand = {
  meta: { category: 'youtube', adminOnly: true, hidden: false },
  data: adminOnly(
    new SlashCommandBuilder()
      .setName('youtube-posli-znovu')
      .setDescription('Pošle poslední video znovu.')
  ),
  async execute(context, interaction) {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    const video = await context.services.youtube.resendLastVideo();
    await interaction.editReply(`Poslal jsem znovu video ${video.video_id}.`);
  }
};

export function getYoutubeAdminCommands() {
  return [youtubeCheckCommand, youtubeRefreshCommand, youtubeResendCommand];
}
