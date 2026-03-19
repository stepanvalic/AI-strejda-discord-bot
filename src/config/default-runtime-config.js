export const defaultRuntimeConfig = Object.freeze({
  guild: {
    guildId: '',
    welcomeChannelId: '',
    defaultRoleId: ''
  },
  discord: {
    activityTexts: ['/help'],
    rules: [],
    inviteMaxAgeSeconds: 0,
    inviteMaxUses: 0
  },
  reactionRoles: {
    channelId: '',
    messageId: '',
    mappings: []
  },
  youtube: {
    channelHandleOrId: '',
    notificationChannelId: '',
    pingRoleId: '',
    checkIntervalSeconds: 300,
    refreshIntervalSeconds: 1800,
    newVideoMaxAgeHours: 24
  },
  counting: {
    channelId: '',
    topicPrefix: 'Counting',
    slowmodeSeconds: 0
  },
  ai: {
    enabled: true,
    model: 'gemini-2.5-flash',
    messagesBatch: 8,
    moderationChannelIds: [],
    positiveThresholds: [2500, 5000, 10000],
    negativeThreshold: -1500,
    veryNegativeThreshold: 80,
    negativePenalty: 150,
    positiveRoleIds: ['', '', ''],
    negativeRoleId: ''
  },
  summary: {
    enabled: true,
    provider: 'deepseek',
    sourceChannelId: '',
    targetChannelId: '',
    cooldownHours: 6,
    dailyHour: 3,
    retentionDays: 30,
    debug: false
  },
  audit: {
    enabled: true,
    channelId: ''
  },
  features: {
    welcome: true,
    reactionRoles: true,
    wordFilter: true,
    bookmarks: true,
    counting: true,
    youtube: true,
    ai: true,
    summary: true,
    audit: true
  },
  setup: {
    channelNames: {
      youtube: 'youtube-notifikace',
      counting: 'counting',
      summary: 'daily-shrnuti',
      audit: 'audit-log'
    },
    categoryName: 'strejda'
  }
});
