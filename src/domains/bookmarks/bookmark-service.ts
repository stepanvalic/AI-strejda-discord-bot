import type { Logger } from "pino";

export class BookmarkService {
  constructor(private readonly logger: Logger) {}

  buildUsageNotes(): string[] {
    return [
      "Slash varianta pouziva `message-link` misto reply-only flow.",
      "Listing pocita se strankovanim po 5 polozkach do DM.",
      "Perzistence jeste neni dopojena na uloziste.",
    ];
  }

  touch(): void {
    this.logger.debug("Bookmark service wired");
  }
}
