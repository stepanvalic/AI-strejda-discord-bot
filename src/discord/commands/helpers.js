import { ChannelType, PermissionFlagsBits } from 'discord.js';
import { chunkText } from '../../shared/utils.js';

export function adminOnly(builder) {
  return builder
    .setDefaultMemberPermissions(PermissionFlagsBits.Administrator)
    .setDMPermission(false);
}

export function guildOnly(builder) {
  return builder.setDMPermission(false);
}

export async function sendChunksToDm(user, title, text) {
  const dm = await user.createDM();

  for (const chunk of chunkText(text, 1900)) {
    await dm.send({
      embeds: [
        {
          title,
          description: chunk
        }
      ]
    });
  }
}

export function parseSummaryDateInput(input, fallback) {
  if (!input) {
    return fallback;
  }

  if (/^\d{4}-\d{2}-\d{2}$/u.test(input)) {
    return input;
  }

  const match = input.match(/^(\d{2})\/(\d{2})\/(\d{4})$/u);
  if (!match) {
    throw new Error('Datum musí být DD/MM/YYYY nebo YYYY-MM-DD.');
  }

  return `${match[3]}-${match[2]}-${match[1]}`;
}

export function ensureTextChannelOption(builder, name, description, required = false) {
  return builder.addChannelOption((option) =>
    option
      .setName(name)
      .setDescription(description)
      .addChannelTypes(ChannelType.GuildText)
      .setRequired(required)
  );
}
