import { Client } from 'discord.js';
import { createContext } from './create-context.js';
import { createServices } from './create-services.js';
import { getCommands } from '../discord/commands/index.js';
import { getClientOptions, registerEventHandlers } from '../discord/register-event-handlers.js';

export async function bootstrap() {
  const context = await createContext();
  context.services = createServices(context);
  const config = await context.configStore.get();
  const commands = getCommands(config);
  context.commands = commands;
  context.commandMap = new Map(commands.map((command) => [command.data.name, command]));
  context.client = new Client(getClientOptions());
  registerEventHandlers(context);

  if (!context.env.DISCORD_TOKEN) {
    throw new Error('Chybí DISCORD_TOKEN v .env.');
  }

  if (!context.guildId) {
    throw new Error('Chybí DISCORD_GUILD_ID v .env nebo guild.guildId v runtime configu.');
  }

  await context.client.login(context.env.DISCORD_TOKEN);
  return context;
}
