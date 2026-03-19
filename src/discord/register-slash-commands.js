import { resolveGuildId } from '../shared/utils.js';
import { REST, Routes } from 'discord.js';

export async function registerSlashCommands({ env, configStore, commands }) {
  if (!env.DISCORD_TOKEN || !env.DISCORD_CLIENT_ID) {
    throw new Error('Chybí DISCORD_TOKEN nebo DISCORD_CLIENT_ID.');
  }

  const config = await configStore.get();

  const guildId = resolveGuildId(env.DISCORD_GUILD_ID, config.guild.guildId);

  if (!guildId) {
    throw new Error('Chybí DISCORD_GUILD_ID v .env nebo guild.guildId v runtime configu.');
  }

  const rest = new REST({ version: '10' }).setToken(env.DISCORD_TOKEN);
  const body = commands.map((command) => command.data.toJSON());

  await rest.put(
    Routes.applicationGuildCommands(env.DISCORD_CLIENT_ID, guildId),
    { body }
  );
}
