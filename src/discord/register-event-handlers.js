import {
  Events,
  GatewayIntentBits,
  MessageFlags,
  Partials
} from 'discord.js';
import { startSchedulers } from '../infrastructure/scheduler/start-schedulers.js';

export function getClientOptions() {
  return {
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMembers,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.GuildMessageReactions,
      GatewayIntentBits.GuildModeration
    ],
    partials: [Partials.Message, Partials.Channel, Partials.Reaction]
  };
}

export function registerEventHandlers(context) {
  const { client, logger, services } = context;

  context.internalEvents.on('audit:moderation', async (payload) => {
    await services.audit.logModerationEvent(payload).catch((error) => logger.warn({ err: error }, 'Audit moderation selhal.'));
  });

  client.once(Events.ClientReady, async () => {
    logger.info({ user: client.user.tag }, 'Discord klient je ready.');
    await services.utility.setPresence().catch((error) => logger.warn({ err: error }, 'Nepodarilo se nastavit activity.'));
    const config = await context.configStore.get();
    const guild = client.guilds.cache.get(context.guildId);

    if (guild && config.features.reactionRoles && config.reactionRoles.channelId) {
      await services.reactionRoles.syncMessage(guild).catch((error) => logger.warn({ err: error }, 'Reaction role sync selhal.'));
    }

    startSchedulers(context);
  });

  client.on(Events.GuildMemberAdd, async (member) => {
    try {
      if (member.guild.id !== context.guildId) {
        return;
      }

      await services.welcome.rewelcome(member);
    } catch (error) {
      logger.warn({ err: error }, 'Welcome flow selhal.');
    }
  });

  client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isChatInputCommand()) {
      return;
    }

    if (interaction.guildId !== context.guildId) {
      return;
    }

    const command = context.commandMap.get(interaction.commandName);
    if (!command) {
      return;
    }

    try {
      logger.info({ command: interaction.commandName, user: interaction.user.id }, 'Slash command zavolany.');
      await command.execute(context, interaction);
    } catch (error) {
      logger.error({ err: error, command: interaction.commandName }, 'Slash command spadl.');
      const payload = {
        content: error.message || 'Něco spadlo.',
        flags: MessageFlags.Ephemeral
      };

      if (interaction.deferred || interaction.replied) {
        await interaction.followUp(payload).catch(() => null);
      } else {
        await interaction.reply(payload).catch(() => null);
      }
    }
  });

  client.on(Events.MessageCreate, async (message) => {
    try {
      if (!message.guild || message.guild.id !== context.guildId) {
        return;
      }

      const blocked = await services.wordFilter.handleMessage(message);
      if (blocked) {
        return;
      }

      await services.summary.captureMessage(message);
      await services.counting.handleMessage(message);
      await services.ai.handleMessage(message);
    } catch (error) {
      logger.warn({ err: error }, 'Message pipeline spadla.');
    }
  });

  client.on(Events.MessageDelete, async (message) => {
    if (!message.guild || message.guild.id !== context.guildId || message.author?.bot) {
      return;
    }

    await services.audit.logMessageDelete(message).catch(() => null);
    await services.counting.restoreLastValidMessage(message).catch(() => null);
  });

  client.on(Events.MessageUpdate, async (oldMessage, newMessage) => {
    if (!newMessage.guild || newMessage.guild.id !== context.guildId || newMessage.author?.bot) {
      return;
    }

    await services.audit.logMessageUpdate(oldMessage, newMessage).catch(() => null);
    await services.counting.restoreLastValidMessage(newMessage).catch(() => null);
  });

  client.on(Events.MessageReactionAdd, async (reaction, user) => {
    await services.reactionRoles.handleReactionChange(reaction, user, true).catch(() => null);
  });

  client.on(Events.MessageReactionRemove, async (reaction, user) => {
    await services.reactionRoles.handleReactionChange(reaction, user, false).catch(() => null);
  });

  client.on(Events.GuildMemberUpdate, async (oldMember, newMember) => {
    if (newMember.guild.id !== context.guildId) {
      return;
    }

    await services.audit.logMemberUpdate(oldMember, newMember).catch(() => null);
  });

  client.on(Events.ChannelCreate, async (channel) => {
    if (channel.guild?.id !== context.guildId) {
      return;
    }

    await services.audit.logChannelCreate(channel).catch(() => null);
  });

  client.on(Events.ChannelDelete, async (channel) => {
    if (channel.guild?.id !== context.guildId) {
      return;
    }

    await services.audit.logChannelDelete(channel).catch(() => null);
  });

  client.on(Events.ChannelUpdate, async (oldChannel, newChannel) => {
    if (newChannel.guild?.id !== context.guildId) {
      return;
    }

    await services.audit.logChannelUpdate(oldChannel, newChannel).catch(() => null);
  });

  client.on(Events.RoleCreate, async (role) => {
    if (role.guild.id !== context.guildId) {
      return;
    }

    await services.audit.logRoleCreate(role).catch(() => null);
  });

  client.on(Events.RoleDelete, async (role) => {
    if (role.guild.id !== context.guildId) {
      return;
    }

    await services.audit.logRoleDelete(role).catch(() => null);
  });

  client.on(Events.RoleUpdate, async (oldRole, newRole) => {
    if (newRole.guild.id !== context.guildId) {
      return;
    }

    await services.audit.logRoleUpdate(oldRole, newRole).catch(() => null);
  });

  client.on(Events.GuildBanAdd, async (ban) => {
    if (ban.guild.id !== context.guildId) {
      return;
    }

    await services.audit.logBan(ban.guild, ban.user).catch(() => null);
  });

  client.on(Events.GuildBanRemove, async (ban) => {
    if (ban.guild.id !== context.guildId) {
      return;
    }

    await services.audit.logUnban(ban.guild, ban.user).catch(() => null);
  });
}
