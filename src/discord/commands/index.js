import { getAiCommands } from './ai.js';
import { getBookmarkCommands } from './bookmarks.js';
import { getCountingCommands } from './counting.js';
import { getModerationCommands } from './moderation.js';
import { getOnboardingCommands } from './onboarding.js';
import { getSetupCommands } from './setup.js';
import { getSummaryCommands } from './summary.js';
import { getUtilityCommands } from './utility.js';
import { getYoutubeAdminCommands } from './youtube-admin.js';

export function getCommands(config) {
  const commands = [
    ...getUtilityCommands(),
    ...getOnboardingCommands(),
    ...getModerationCommands(),
    ...getCountingCommands(),
    ...getAiCommands(),
    ...getSummaryCommands(),
    ...getBookmarkCommands(),
    ...getSetupCommands(),
    ...getYoutubeAdminCommands()
  ];

  if (config?.features?.setup === false) {
    return commands.filter((command) => command.meta.category !== 'setup');
  }

  return commands;
}
