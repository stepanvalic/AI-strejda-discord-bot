import { z } from 'zod';

const roleMappingSchema = z.object({
  roleId: z.string(),
  emoji: z.string().min(1),
  description: z.string().min(1)
});

export const envSchema = z.object({
  DISCORD_TOKEN: z.string().optional(),
  DISCORD_CLIENT_ID: z.string().optional(),
  DISCORD_GUILD_ID: z.string().default(''),
  YOUTUBE_API_KEY: z.string().optional(),
  GEMINI_API_KEY: z.string().optional(),
  DEEPSEEK_API_KEY: z.string().optional(),
  BOT_CONFIG_PATH: z.string().default('config/runtime.local.json'),
  DATA_DIR: z.string().default('db'),
  SUMMARY_DIR: z.string().default('db/sumar'),
  LOG_LEVEL: z.string().default('info'),
  TIMEZONE: z.string().default('Europe/Prague')
});

export const runtimeConfigSchema = z.object({
  guild: z.object({
    guildId: z.string().default(''),
    welcomeChannelId: z.string().default(''),
    defaultRoleId: z.string().default('')
  }),
  discord: z.object({
    activityTexts: z.array(z.string()).default([]),
    rules: z.array(z.string()).default([]),
    inviteMaxAgeSeconds: z.number().int().nonnegative().default(0),
    inviteMaxUses: z.number().int().nonnegative().default(0)
  }),
  reactionRoles: z.object({
    channelId: z.string().default(''),
    messageId: z.string().default(''),
    mappings: z.array(roleMappingSchema).default([])
  }),
  youtube: z.object({
    channelHandleOrId: z.string().default(''),
    notificationChannelId: z.string().default(''),
    pingRoleId: z.string().default(''),
    checkIntervalSeconds: z.number().int().positive().default(300),
    refreshIntervalSeconds: z.number().int().positive().default(1800),
    newVideoMaxAgeHours: z.number().int().positive().default(24)
  }),
  counting: z.object({
    channelId: z.string().default(''),
    topicPrefix: z.string().default('Counting'),
    slowmodeSeconds: z.number().int().nonnegative().default(0)
  }),
  ai: z.object({
    enabled: z.boolean().default(true),
    model: z.string().default('gemini-2.5-flash'),
    messagesBatch: z.number().int().positive().default(8),
    moderationChannelIds: z.array(z.string()).default([]),
    positiveThresholds: z.array(z.number().int()).length(3).default([2500, 5000, 10000]),
    negativeThreshold: z.number().int().default(-1500),
    veryNegativeThreshold: z.number().int().default(80),
    negativePenalty: z.number().int().positive().default(150),
    positiveRoleIds: z.array(z.string()).length(3).default(['', '', '']),
    negativeRoleId: z.string().default('')
  }),
  summary: z.object({
    enabled: z.boolean().default(true),
    provider: z.enum(['deepseek']).default('deepseek'),
    sourceChannelId: z.string().default(''),
    targetChannelId: z.string().default(''),
    cooldownHours: z.number().int().positive().default(6),
    dailyHour: z.number().int().min(0).max(23).default(3),
    retentionDays: z.number().int().positive().default(30),
    debug: z.boolean().default(false)
  }),
  audit: z.object({
    enabled: z.boolean().default(true),
    channelId: z.string().default('')
  }),
  features: z.object({
    welcome: z.boolean().default(true),
    reactionRoles: z.boolean().default(true),
    wordFilter: z.boolean().default(true),
    bookmarks: z.boolean().default(true),
    counting: z.boolean().default(true),
    youtube: z.boolean().default(true),
    ai: z.boolean().default(true),
    summary: z.boolean().default(true),
    audit: z.boolean().default(true)
  }),
  setup: z.object({
    channelNames: z.object({
      youtube: z.string().default('youtube-notifikace'),
      counting: z.string().default('counting'),
      summary: z.string().default('daily-shrnuti'),
      audit: z.string().default('audit-log')
    }),
    categoryName: z.string().default('strejda')
  })
});
