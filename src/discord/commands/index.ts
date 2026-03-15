import type { SlashCommandModule } from "./types.js";
import { aiCommand } from "./ai.command.js";
import { bookmarkCommand } from "./bookmark.command.js";
import { countingCommand } from "./counting.command.js";
import { moderationCommand } from "./moderation.command.js";
import { onboardingCommand } from "./onboarding.command.js";
import { setupCommand } from "./setup.command.js";
import { summaryCommand } from "./summary.command.js";
import { systemCommand } from "./system.command.js";
import { utilityCommand } from "./utility.command.js";
import { youtubeAdminCommand } from "./youtube-admin.command.js";

export const slashCommands: SlashCommandModule[] = [
  utilityCommand,
  onboardingCommand,
  moderationCommand,
  countingCommand,
  aiCommand,
  summaryCommand,
  bookmarkCommand,
  setupCommand,
  youtubeAdminCommand,
  systemCommand,
];

export const commandMap = new Map(slashCommands.map((command) => [command.name, command]));
