import { createContext } from '../src/app/create-context.js';
import { getCommands } from '../src/discord/commands/index.js';
import { registerSlashCommands } from '../src/discord/register-slash-commands.js';

const context = await createContext();
const config = await context.configStore.get();
const commands = getCommands(config);

await registerSlashCommands({
  env: context.env,
  configStore: context.configStore,
  commands
});

context.logger.info({ count: commands.length }, 'Slash commandy zaregistrovany.');
