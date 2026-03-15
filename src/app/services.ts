import type { Logger } from "pino";

import type { BotConfig } from "../config/types.js";
import { AiScoringService } from "../domains/ai-scoring/ai-scoring-service.js";
import { AuditService } from "../domains/audit/audit-service.js";
import { BookmarkService } from "../domains/bookmarks/bookmark-service.js";
import { CountingService } from "../domains/counting/counting-service.js";
import { ModerationService } from "../domains/moderation/moderation-service.js";
import { ReactionRoleService } from "../domains/reaction-roles/reaction-role-service.js";
import { SetupService } from "../domains/setup/setup-service.js";
import { SummaryService } from "../domains/summary/summary-service.js";
import { SystemService } from "../domains/system/system-service.js";
import { UtilityService } from "../domains/utility/utility-service.js";
import { WelcomeService } from "../domains/welcome/welcome-service.js";
import { WordFilterService } from "../domains/word-filter/word-filter-service.js";
import { YoutubeService } from "../domains/youtube/youtube-service.js";

export interface DomainServices {
  utility: UtilityService;
  welcome: WelcomeService;
  reactionRoles: ReactionRoleService;
  moderation: ModerationService;
  counting: CountingService;
  aiScoring: AiScoringService;
  summary: SummaryService;
  bookmarks: BookmarkService;
  setup: SetupService;
  youtube: YoutubeService;
  audit: AuditService;
  wordFilter: WordFilterService;
  system: SystemService;
}

export const createServices = (config: BotConfig, logger: Logger, startedAt: Date): DomainServices => ({
  utility: new UtilityService(config, startedAt),
  welcome: new WelcomeService(config, logger),
  reactionRoles: new ReactionRoleService(config, logger),
  moderation: new ModerationService(logger),
  counting: new CountingService(config, logger),
  aiScoring: new AiScoringService(config, logger),
  summary: new SummaryService(config, logger),
  bookmarks: new BookmarkService(logger),
  setup: new SetupService(logger),
  youtube: new YoutubeService(config, logger),
  audit: new AuditService(logger),
  wordFilter: new WordFilterService(logger),
  system: new SystemService(logger),
});
