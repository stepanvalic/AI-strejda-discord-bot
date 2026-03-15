import { z } from "zod";

const normalizeString = (value: unknown): string | undefined => {
  if (typeof value !== "string") {
    return undefined;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
};

const requiredString = z.preprocess(
  (value) => normalizeString(value),
  z.string().min(1),
);

const optionalString = z.preprocess(
  (value) => normalizeString(value),
  z.string().min(1).optional(),
);

const optionalInt = z.preprocess((value) => {
  const normalized = normalizeString(value);
  if (normalized === undefined) {
    return undefined;
  }

  const parsed = Number.parseInt(normalized, 10);
  return Number.isNaN(parsed) ? normalized : parsed;
}, z.number().int().optional());

const requiredInt = z.preprocess((value) => {
  const normalized = normalizeString(value);
  if (normalized === undefined) {
    return undefined;
  }

  const parsed = Number.parseInt(normalized, 10);
  return Number.isNaN(parsed) ? normalized : parsed;
}, z.number().int());

const optionalBoolean = z.preprocess((value) => {
  const normalized = normalizeString(value)?.toLowerCase();
  if (normalized === undefined) {
    return undefined;
  }

  if (["true", "1", "yes", "on"].includes(normalized)) {
    return true;
  }

  if (["false", "0", "no", "off"].includes(normalized)) {
    return false;
  }

  return normalized;
}, z.boolean().optional());

export const envSchema = z.object({
  DISCORD_TOKEN: requiredString,
  APPLICATION_ID: requiredString,
  GUILD_ID: requiredString,
  BOT_CONFIG_FILE: optionalString,
  BOT_TIMEZONE: optionalString,
  AUTO_REGISTER_SLASH_COMMANDS: optionalBoolean,
  WELCOME_CHANNEL_ID: optionalString,
  YOUTUBE_NOTIFICATION_CHANNEL_ID: optionalString,
  COUNTING_CHANNEL_ID: optionalString,
  AUDIT_LOG_CHANNEL_ID: optionalString,
  SUMMARY_CHAT_ID: optionalString,
  SUMMARY_CHANNEL_ID: optionalString,
  REACTION_ROLES_CHANNEL_ID: optionalString,
  REACTION_ROLES_MESSAGE_ID: optionalString,
  DEFAULT_ROLE_ID: optionalString,
  YOUTUBE_PING_ROLE_ID: optionalString,
  AI_POSITIVE_ROLE_ID_1: optionalString,
  AI_POSITIVE_ROLE_ID_2: optionalString,
  AI_POSITIVE_ROLE_ID_3: optionalString,
  AI_NEGATIVE_ROLE_ID: optionalString,
  ACTIVITY_TEXT_1: optionalString,
  ACTIVITY_TEXT_2: optionalString,
  ACTIVITY_TEXT_3: optionalString,
  COUNTING_TOPIC_PREFIX: optionalString,
  REACTION_ROLES_MAPPINGS: optionalString,
  YOUTUBE_CHANNEL_ID: optionalString,
  CHECK_INTERVAL_SECONDS: optionalInt,
  NEW_VIDEO_MAX_AGE_HOURS: optionalInt,
  AI_MODEL: optionalString,
  AI_MESSAGES_BATCH: optionalInt,
  AI_MODERATION_SAVE_FILE: optionalString,
  AI_MODERATION_INTERVAL_MINUTES: optionalInt,
  AI_MODERATION_CHANNEL_IDS: optionalString,
  AI_POSITIVE_THRESHOLD_1: optionalInt,
  AI_POSITIVE_THRESHOLD_2: optionalInt,
  AI_POSITIVE_THRESHOLD_3: optionalInt,
  AI_NEGATIVE_THRESHOLD: optionalInt,
  AI_VERY_NEGATIVE_THRESHOLD: optionalInt,
  AI_NEGATIVE_PENALTY: optionalInt,
  SUMMARY_API_PROVIDER: optionalString,
  DEEPSEEK_MODEL: optionalString,
  SUMMARY_COOLDOWN_HOURS: optionalInt,
  SUMMARY_DEBUG: optionalBoolean,
  LOG_LEVEL: optionalString,
  LOG_MAX_SIZE: optionalInt,
  LOG_BACKUP_COUNT: optionalInt,
  COUNTING_SAVE_FILE: optionalString,
  DISCORD_INVITE_MAX_AGE: optionalInt,
  DISCORD_INVITE_MAX_USES: optionalInt,
  YOUTUBE_API_KEY: optionalString,
  GEMINI_API_KEY: optionalString,
  DEEPSEEK_API_KEY: optionalString,
  OPENROUTER_API_KEY: optionalString,
});

export const publicConfigSchema = z.object({
  branding: z
    .object({
      embedColor: z.string().default("#f5b942"),
      footerText: z.string().default("AI Strejda"),
    })
    .default({}),
  texts: z
    .object({
      activityTexts: z.array(z.string()).default([]),
      countingTopicPrefix: z.string().optional(),
      serverRules: z.array(z.string()).default([]),
    })
    .default({}),
  reactionRoles: z
    .array(
      z.object({
        roleId: z.string().min(1),
        emoji: z.string().min(1),
        description: z.string().min(1),
      }),
    )
    .default([]),
  features: z
    .object({
      welcome: z.boolean().default(true),
      reactionRoles: z.boolean().default(true),
      utility: z.boolean().default(true),
      moderation: z.boolean().default(true),
      audit: z.boolean().default(true),
      wordFilter: z.boolean().default(true),
      bookmarks: z.boolean().default(true),
      youtube: z.boolean().default(true),
      counting: z.boolean().default(true),
      aiScoring: z.boolean().default(true),
      summary: z.boolean().default(true),
    })
    .default({}),
  youtube: z
    .object({
      channelUrl: z.string().url().optional(),
    })
    .default({}),
});

export type RawEnv = z.infer<typeof envSchema>;
export type PublicConfig = z.infer<typeof publicConfigSchema>;

export { requiredInt };
