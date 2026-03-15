import {
  ActivityType,
  ChatInputCommandInteraction,
  Events,
  type Client,
  type GuildChannel,
  type Message,
  type PartialMessage,
} from "discord.js";

import type { AppContext } from "../app/context.js";
import { commandMap } from "./commands/index.js";
import { createBaseEmbed } from "./commands/support/response.js";

const cycleActivities = (client: Client, context: AppContext) => {
  const activities = context.config.texts.activityTexts;
  if (activities.length === 0) {
    return;
  }

  let index = 0;
  const applyActivity = () => {
    const name = activities[index] ?? activities[0];
    client.user?.setActivity(name, { type: ActivityType.Watching });
    index = (index + 1) % activities.length;
  };

  applyActivity();
  setInterval(applyActivity, 30_000).unref();
};

const reportInteractionError = async (
  context: AppContext,
  error: unknown,
  interaction: ChatInputCommandInteraction,
) => {
  context.logger.error({ error }, "Slash command failed");

  const embed = createBaseEmbed(
    context,
    "Command spadnul",
    error instanceof Error ? error.message : "Neznama chyba pri vykonavani commandu.",
  );

  if (interaction.replied || interaction.deferred) {
    await interaction.followUp({ embeds: [embed], ephemeral: true }).catch(() => undefined);
    return;
  }

  await interaction.reply({ embeds: [embed], ephemeral: true }).catch(() => undefined);
};

const handleMessageCreate = async (context: AppContext, message: Message) => {
  if (message.author.bot || !message.guild) {
    return;
  }

  await Promise.all([
    context.config.features.wordFilter ? context.services.wordFilter.handleMessageCreate(message) : undefined,
    context.config.features.counting ? context.services.counting.handleMessageCreate(message) : undefined,
    context.config.features.aiScoring ? context.services.aiScoring.handleMessageCreate(message) : undefined,
    context.config.features.summary ? context.services.summary.handleMessageCreate(message) : undefined,
  ]);
};

const handleMessageUpdate = async (
  context: AppContext,
  oldMessage: Message | PartialMessage,
  newMessage: Message | PartialMessage,
) => {
  await Promise.all([
    context.config.features.counting ? context.services.counting.handleMessageUpdate(oldMessage, newMessage) : undefined,
    context.config.features.audit ? context.services.audit.handleMessageUpdate(oldMessage, newMessage) : undefined,
  ]);
};

const handleMessageDelete = async (context: AppContext, message: Message | PartialMessage) => {
  await Promise.all([
    context.config.features.counting ? context.services.counting.handleMessageDelete(message) : undefined,
    context.config.features.audit ? context.services.audit.handleMessageDelete(message) : undefined,
  ]);
};

export const registerDiscordEvents = (client: Client, context: AppContext) => {
  client.once(Events.ClientReady, async (readyClient) => {
    context.logger.info({ userTag: readyClient.user.tag }, "Discord client ready");
    cycleActivities(client, context);

    if (context.config.features.reactionRoles && readyClient.guilds.cache.has(context.config.discord.guildId)) {
      const guild = await readyClient.guilds.fetch(context.config.discord.guildId).catch(() => null);
      if (guild) {
        await context.services.reactionRoles.syncReactionRoleMessage(guild).catch((error) => {
          context.logger.warn({ error }, "Reaction role sync is not wired yet");
        });
      }
    }
  });

  client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isChatInputCommand()) {
      return;
    }

    const command = commandMap.get(interaction.commandName);
    if (!command) {
      const embed = createBaseEmbed(context, "Neznamy command", `Command \`${interaction.commandName}\` neni v registru.`);
      await interaction.reply({ embeds: [embed], ephemeral: true }).catch(() => undefined);
      return;
    }

    try {
      await command.execute(interaction, context);
    } catch (error) {
      await reportInteractionError(context, error, interaction);
    }
  });

  client.on(Events.GuildMemberAdd, async (member) => {
    if (!context.config.features.welcome) {
      return;
    }

    await context.services.welcome.sendWelcome(member).catch((error) => {
      context.logger.error({ error, memberId: member.id }, "Welcome flow failed");
    });
  });

  client.on(Events.MessageCreate, async (message) => {
    await handleMessageCreate(context, message).catch((error) => {
      context.logger.error({ error, messageId: message.id }, "MessageCreate pipeline failed");
    });
  });

  client.on(Events.MessageUpdate, async (oldMessage, newMessage) => {
    await handleMessageUpdate(context, oldMessage, newMessage).catch((error) => {
      context.logger.error({ error }, "MessageUpdate pipeline failed");
    });
  });

  client.on(Events.MessageDelete, async (message) => {
    await handleMessageDelete(context, message).catch((error) => {
      context.logger.error({ error }, "MessageDelete pipeline failed");
    });
  });

  client.on(Events.MessageReactionAdd, async (reaction, user) => {
    if (!context.config.features.reactionRoles) {
      return;
    }

    await context.services.reactionRoles.handleReactionAdd(reaction, user).catch((error) => {
      context.logger.error({ error }, "Reaction add pipeline failed");
    });
  });

  client.on(Events.MessageReactionRemove, async (reaction, user) => {
    if (!context.config.features.reactionRoles) {
      return;
    }

    await context.services.reactionRoles.handleReactionRemove(reaction, user).catch((error) => {
      context.logger.error({ error }, "Reaction remove pipeline failed");
    });
  });

  client.on(Events.GuildMemberUpdate, async (oldMember, newMember) => {
    if (!context.config.features.audit) {
      return;
    }

    await context.services.audit.handleGuildMemberUpdate(oldMember, newMember).catch((error) => {
      context.logger.error({ error }, "GuildMemberUpdate pipeline failed");
    });
  });

  client.on(Events.ChannelCreate, async (channel) => {
    if (!context.config.features.audit || !channel.isTextBased()) {
      return;
    }

    await context.services.audit.handleChannelCreate(channel as GuildChannel).catch((error) => {
      context.logger.error({ error }, "ChannelCreate pipeline failed");
    });
  });

  client.on(Events.ChannelDelete, async (channel) => {
    if (!context.config.features.audit || !channel.isTextBased()) {
      return;
    }

    await context.services.audit.handleChannelDelete(channel as GuildChannel).catch((error) => {
      context.logger.error({ error }, "ChannelDelete pipeline failed");
    });
  });

  client.on(Events.ChannelUpdate, async (oldChannel, newChannel) => {
    if (!context.config.features.audit || !newChannel.isTextBased() || !oldChannel.isTextBased()) {
      return;
    }

    await context.services.audit.handleChannelUpdate(oldChannel as GuildChannel, newChannel as GuildChannel).catch((error) => {
      context.logger.error({ error }, "ChannelUpdate pipeline failed");
    });
  });

  client.on(Events.GuildBanAdd, async (ban) => {
    if (!context.config.features.audit) {
      return;
    }

    await context.services.audit.handleGuildBanAdd(ban).catch((error) => {
      context.logger.error({ error }, "GuildBanAdd pipeline failed");
    });
  });

  client.on(Events.GuildBanRemove, async (ban) => {
    if (!context.config.features.audit) {
      return;
    }

    await context.services.audit.handleGuildBanRemove(ban).catch((error) => {
      context.logger.error({ error }, "GuildBanRemove pipeline failed");
    });
  });

  client.on(Events.GuildRoleCreate, async (role) => {
    if (!context.config.features.audit) {
      return;
    }

    await context.services.audit.handleRoleCreate(role).catch((error) => {
      context.logger.error({ error }, "GuildRoleCreate pipeline failed");
    });
  });

  client.on(Events.GuildRoleDelete, async (role) => {
    if (!context.config.features.audit) {
      return;
    }

    await context.services.audit.handleRoleDelete(role).catch((error) => {
      context.logger.error({ error }, "GuildRoleDelete pipeline failed");
    });
  });

  client.on(Events.GuildRoleUpdate, async (oldRole, newRole) => {
    if (!context.config.features.audit) {
      return;
    }

    await context.services.audit.handleRoleUpdate(oldRole, newRole).catch((error) => {
      context.logger.error({ error }, "GuildRoleUpdate pipeline failed");
    });
  });
};
