export type LogLevel = "trace" | "debug" | "info" | "warn" | "error" | "fatal";

export interface ReactionRoleMapping {
  roleId: string;
  emoji: string;
  description: string;
}

export interface FeatureFlags {
  welcome: boolean;
  reactionRoles: boolean;
  utility: boolean;
  moderation: boolean;
  audit: boolean;
  wordFilter: boolean;
  bookmarks: boolean;
  youtube: boolean;
  counting: boolean;
  aiScoring: boolean;
  summary: boolean;
}

export interface BotConfig {
  discord: {
    token: string;
    applicationId: string;
    guildId: string;
    inviteMaxAge: number;
    inviteMaxUses: number;
  };
  runtime: {
    timezone: string;
    autoRegisterSlashCommands: boolean;
    configFilePath: string;
  };
  channels: {
    welcomeChannelId?: string;
    youtubeNotificationChannelId?: string;
    countingChannelId?: string;
    auditLogChannelId?: string;
    summaryChatId?: string;
    summaryChannelId?: string;
    reactionRolesChannelId?: string;
    reactionRolesMessageId?: string;
  };
  roles: {
    defaultRoleId?: string;
    youtubePingRoleId?: string;
    aiPositiveRoleIds: string[];
    aiNegativeRoleId?: string;
  };
  texts: {
    activityTexts: string[];
    countingTopicPrefix: string;
    serverRules: string[];
    reactionRoles: ReactionRoleMapping[];
  };
  youtube: {
    channelId?: string;
    channelUrl?: string;
    checkIntervalSeconds: number;
    newVideoMaxAgeHours: number;
  };
  ai: {
    model: string;
    messagesBatch: number;
    moderationSaveFile: string;
    moderationIntervalMinutes: number;
    moderationChannelIds: string[];
    positiveThresholds: number[];
    negativeThreshold: number;
    veryNegativeThreshold: number;
    negativePenalty: number;
  };
  summary: {
    provider: string;
    deepseekModel: string;
    cooldownHours: number;
    debug: boolean;
  };
  logging: {
    level: LogLevel;
    maxSize: number;
    backupCount: number;
  };
  paths: {
    countingSaveFile: string;
  };
  secrets: {
    youtubeApiKey?: string;
    geminiApiKey?: string;
    deepseekApiKey?: string;
    openrouterApiKey?: string;
  };
  features: FeatureFlags;
  branding: {
    embedColor: number;
    footerText: string;
  };
}
