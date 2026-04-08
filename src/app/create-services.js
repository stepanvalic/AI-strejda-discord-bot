import { AiScoringService } from '../domains/ai-scoring/service.js';
import { AuditService } from '../domains/audit/service.js';
import { BookmarkService } from '../domains/bookmarks/service.js';
import { CountingService } from '../domains/counting/service.js';
import { ReactionRoleService } from '../domains/reaction-roles/service.js';
import { SummaryService } from '../domains/summary/service.js';
import { SetupService, UtilityService } from '../domains/utility/service.js';
import { WelcomeService } from '../domains/welcome/service.js';
import { WordFilterService } from '../domains/word-filter/service.js';
import { YoutubeService } from '../domains/youtube/service.js';

export function createServices(context) {
  return {
    utility: new UtilityService(context),
    setup: new SetupService(context),
    welcome: new WelcomeService(context),
    reactionRoles: new ReactionRoleService(context),
    audit: new AuditService(context),
    wordFilter: new WordFilterService(context),
    bookmarks: new BookmarkService(context),
    counting: new CountingService(context),
    ai: new AiScoringService(context),
    summary: new SummaryService(context),
    youtube: new YoutubeService(context)
  };
}
