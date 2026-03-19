import { EventEmitter } from 'node:events';
import { ConfigStore } from '../config/config-store.js';
import { loadEnv } from '../config/load-env.js';
import { createLogger } from '../infrastructure/logging/create-logger.js';
import { JsonDatabase } from '../infrastructure/persistence/database.js';
import { resolveGuildId } from '../shared/utils.js';

export async function createContext() {
  const env = loadEnv();
  const configStore = new ConfigStore(env.BOT_CONFIG_PATH);
  const runtimeConfig = await configStore.get();
  const logger = createLogger(env.LOG_LEVEL || runtimeConfig.logging?.level || 'info');
  const database = new JsonDatabase({
    dataDir: env.DATA_DIR,
    summaryDir: env.SUMMARY_DIR
  });

  await database.ensure();

  return {
    env,
    configStore,
    database,
    logger,
    guildId: resolveGuildId(env.DISCORD_GUILD_ID, runtimeConfig.guild.guildId),
    startedAt: new Date(),
    internalEvents: new EventEmitter(),
    runtime: {
      aiBuffers: new Map(),
      summaryCooldowns: new Map(),
      lastDailySummaryDate: null,
      countingLastValidMessage: null,
      currentActivityIndex: 0
    }
  };
}
