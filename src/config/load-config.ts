import { access, readFile } from "node:fs/promises";
import { constants } from "node:fs";
import path from "node:path";

import dotenv from "dotenv";

import { envSchema, publicConfigSchema, type PublicConfig, type RawEnv } from "./schema.js";
import type { BotConfig, FeatureFlags, ReactionRoleMapping } from "./types.js";

dotenv.config();

const defaultServerRules = [
  "Chovej se normalne a ne jak rozbity toaster.",
  "Spam, scam a vylozene toxicky obsah leti.",
  "V countingu netahni dvakrat po sobe.",
  "AI role jsou reputacni system, ne automat na vyhry.",
];

const defaultFeatureFlags: FeatureFlags = {
  welcome: true,
  reactionRoles: true,
  utility: true,
  moderation: true,
  audit: true,
  wordFilter: true,
  bookmarks: true,
  youtube: true,
  counting: true,
  aiScoring: true,
  summary: true,
};

const parseEmbedColor = (value: string): number => {
  const normalized = value.replace("#", "");
  const parsed = Number.parseInt(normalized, 16);

  if (Number.isNaN(parsed)) {
    return 0xf5b942;
  }

  return parsed;
};

const parseCsv = (value?: string): string[] => {
  if (!value) {
    return [];
  }

  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
};

const parseReactionRoleMappings = (value?: string): ReactionRoleMapping[] => {
  if (!value) {
    return [];
  }

  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => {
      const [roleId, emoji, description] = line.split("=").map((part) => part.trim());
      if (!roleId || !emoji || !description) {
        throw new Error(`Invalid REACTION_ROLES_MAPPINGS line: ${line}`);
      }

      return {
        roleId,
        emoji,
        description,
      };
    });
};

const loadPublicConfig = async (configFilePath: string): Promise<PublicConfig> => {
  const absolutePath = path.resolve(process.cwd(), configFilePath);

  try {
    await access(absolutePath, constants.F_OK);
  } catch {
    return publicConfigSchema.parse({});
  }

  const raw = await readFile(absolutePath, "utf8");
  const parsed = JSON.parse(raw) as unknown;
  return publicConfigSchema.parse(parsed);
};

const buildActivityTexts = (env: RawEnv, publicConfig: PublicConfig): string[] => {
  if (publicConfig.texts.activityTexts.length > 0) {
    return publicConfig.texts.activityTexts;
  }

  const candidates = [env.ACTIVITY_TEXT_1, env.ACTIVITY_TEXT_2, env.ACTIVITY_TEXT_3].filter(
    (value): value is string => Boolean(value),
  );

  return candidates.length > 0
    ? candidates
    : ["hlida slash commandy", "kouka na YouTube", "drzi counting v lati"];
};

const buildReactionRoles = (env: RawEnv, publicConfig: PublicConfig): ReactionRoleMapping[] => {
  if (publicConfig.reactionRoles.length > 0) {
    return publicConfig.reactionRoles;
  }

  return parseReactionRoleMappings(env.REACTION_ROLES_MAPPINGS);
};

export const loadConfig = async (): Promise<BotConfig> => {
  const env = envSchema.parse(process.env);
  const configFilePath = env.BOT_CONFIG_FILE ?? "./config/bot.config.json";
  const publicConfig = await loadPublicConfig(configFilePath);

  return {
    discord: {
      token: env.DISCORD_TOKEN,
      applicationId: env.APPLICATION_ID,
      guildId: env.GUILD_ID,
      inviteMaxAge: env.DISCORD_INVITE_MAX_AGE ?? 0,
      inviteMaxUses: env.DISCORD_INVITE_MAX_USES ?? 0,
    },
    runtime: {
      timezone: env.BOT_TIMEZONE ?? "Europe/Prague",
      autoRegisterSlashCommands: env.AUTO_REGISTER_SLASH_COMMANDS ?? true,
      configFilePath,
    },
    channels: {
      welcomeChannelId: env.WELCOME_CHANNEL_ID,
      youtubeNotificationChannelId: env.YOUTUBE_NOTIFICATION_CHANNEL_ID,
      countingChannelId: env.COUNTING_CHANNEL_ID,
      auditLogChannelId: env.AUDIT_LOG_CHANNEL_ID,
      summaryChatId: env.SUMMARY_CHAT_ID,
      summaryChannelId: env.SUMMARY_CHANNEL_ID,
      reactionRolesChannelId: env.REACTION_ROLES_CHANNEL_ID,
      reactionRolesMessageId: env.REACTION_ROLES_MESSAGE_ID,
    },
    roles: {
      defaultRoleId: env.DEFAULT_ROLE_ID,
      youtubePingRoleId: env.YOUTUBE_PING_ROLE_ID,
      aiPositiveRoleIds: [
        env.AI_POSITIVE_ROLE_ID_1,
        env.AI_POSITIVE_ROLE_ID_2,
        env.AI_POSITIVE_ROLE_ID_3,
      ].filter((value): value is string => Boolean(value)),
      aiNegativeRoleId: env.AI_NEGATIVE_ROLE_ID,
    },
    texts: {
      activityTexts: buildActivityTexts(env, publicConfig),
      countingTopicPrefix: publicConfig.texts.countingTopicPrefix ?? env.COUNTING_TOPIC_PREFIX ?? "Aktualni cislo",
      serverRules:
        publicConfig.texts.serverRules.length > 0
          ? publicConfig.texts.serverRules
          : defaultServerRules,
      reactionRoles: buildReactionRoles(env, publicConfig),
    },
    youtube: {
      channelId: env.YOUTUBE_CHANNEL_ID,
      channelUrl: publicConfig.youtube.channelUrl,
      checkIntervalSeconds: env.CHECK_INTERVAL_SECONDS ?? 300,
      newVideoMaxAgeHours: env.NEW_VIDEO_MAX_AGE_HOURS ?? 24,
    },
    ai: {
      model: env.AI_MODEL ?? "gemini-2.0-flash",
      messagesBatch: env.AI_MESSAGES_BATCH ?? 5,
      moderationSaveFile: env.AI_MODERATION_SAVE_FILE ?? "./db/ai-moderation.json",
      moderationIntervalMinutes: env.AI_MODERATION_INTERVAL_MINUTES ?? 30,
      moderationChannelIds: parseCsv(env.AI_MODERATION_CHANNEL_IDS),
      positiveThresholds: [
        env.AI_POSITIVE_THRESHOLD_1 ?? 25,
        env.AI_POSITIVE_THRESHOLD_2 ?? 75,
        env.AI_POSITIVE_THRESHOLD_3 ?? 150,
      ],
      negativeThreshold: env.AI_NEGATIVE_THRESHOLD ?? -50,
      veryNegativeThreshold: env.AI_VERY_NEGATIVE_THRESHOLD ?? -80,
      negativePenalty: env.AI_NEGATIVE_PENALTY ?? 15,
    },
    summary: {
      provider: env.SUMMARY_API_PROVIDER ?? "deepseek",
      deepseekModel: env.DEEPSEEK_MODEL ?? "deepseek-chat",
      cooldownHours: env.SUMMARY_COOLDOWN_HOURS ?? 12,
      debug: env.SUMMARY_DEBUG ?? false,
    },
    logging: {
      level: (env.LOG_LEVEL ?? "info") as BotConfig["logging"]["level"],
      maxSize: env.LOG_MAX_SIZE ?? 10_485_760,
      backupCount: env.LOG_BACKUP_COUNT ?? 5,
    },
    paths: {
      countingSaveFile: env.COUNTING_SAVE_FILE ?? "./db/counting.json",
    },
    secrets: {
      youtubeApiKey: env.YOUTUBE_API_KEY,
      geminiApiKey: env.GEMINI_API_KEY,
      deepseekApiKey: env.DEEPSEEK_API_KEY,
      openrouterApiKey: env.OPENROUTER_API_KEY,
    },
    features: {
      ...defaultFeatureFlags,
      ...publicConfig.features,
    },
    branding: {
      embedColor: parseEmbedColor(publicConfig.branding.embedColor),
      footerText: publicConfig.branding.footerText,
    },
  };
};
