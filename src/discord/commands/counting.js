import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { createEmbed } from '../../shared/discord-helpers.js';
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
    await interaction.reply({
      embeds: [await context.services.counting.getStatusEmbed()],
      flags: MessageFlags.Ephemeral
    });
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
    const days = interaction.options.getInteger('dny');
    await context.services.counting.blockUser(member, days);
    await interaction.reply({
      embeds: [
        createEmbed({
          title: '⛔ Uživatel zablokován',
          description: `${member} byl zablokován v countingu.`,
          fields: [
            { name: 'Délka blokace', value: `**${days}** dní`, inline: true }
          ]
        })
      ],
      flags: MessageFlags.Ephemeral
    });
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
    await interaction.reply({
      embeds: [await context.services.counting.getBlockedEmbed()],
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
    await interaction.reply({
      embeds: [
        createEmbed({
          title: '✅ Uživatel odblokován',
          description: `${user} byl odblokován v countingu.`
        })
      ],
      flags: MessageFlags.Ephemeral
    });
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
    await interaction.reply({
      embeds: [
        createEmbed({
          title: '📍 Counting kanál nastaven',
          description: `Nový counting kanál je ${channel}.`
        })
      ],
      flags: MessageFlags.Ephemeral
    });
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
    await interaction.reply({
      embeds: [await context.services.counting.getChannelEmbed()],
      flags: MessageFlags.Ephemeral
    });
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
    await interaction.reply({ embeds: [context.services.counting.getRulesEmbed()] });
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
    await interaction.reply({
      embeds: [await context.services.counting.getStatsEmbed(interaction.guild, user?.id)]
    });
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
    await interaction.reply({ embeds: [context.services.counting.getFormatsEmbed()] });
  }
};

export function getCountingCommands() {
  return [
    statusCommand,
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
