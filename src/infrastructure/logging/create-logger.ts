import pino from "pino";

import type { BotConfig } from "../../config/types.js";

export const createLogger = (config: BotConfig) =>
  pino({
    level: config.logging.level,
    transport:
      process.env.NODE_ENV === "production"
        ? undefined
        : {
            target: "pino-pretty",
            options: {
              colorize: true,
              translateTime: "SYS:standard",
            },
          },
  });
