import path from 'node:path';
import { access, copyFile, mkdir } from 'node:fs/promises';
import { JsonFileStore } from './json-file-store.js';

function createCountingDefault() {
  return {
    current_count: 0,
    high_score: 0,
    last_user_id: null,
    failed_counts: 0,
    user_stats: {},
    blocked_users: {}
  };
}

export class JsonDatabase {
  constructor({ dataDir, summaryDir }) {
    this.dataDir = path.resolve(dataDir);
    this.summaryDir = path.resolve(summaryDir);
    this.bookmarksPath = path.resolve('db', 'bookmarks.json');
    this.legacyBookmarksPath = path.join(this.dataDir, 'bookmarks.json');
    this.counting = new JsonFileStore(path.join(this.dataDir, 'counting.json'), createCountingDefault);
    this.aiModeration = new JsonFileStore(path.join(this.dataDir, 'ai_moderation.json'), () => ({
      users: {},
      last_updated: null
    }));
    this.youtube = new JsonFileStore(path.join(this.dataDir, 'youtube_videos.json'), () => ({ videos: [] }));
    this.chatMessages = new JsonFileStore(path.join(this.dataDir, 'chat_messages.json'), () => ({
      messages: [],
      summaries: []
    }));
    this.moderationArchive = new JsonFileStore(path.join(this.dataDir, 'moderation_messages.json'), () => ({
      messages: []
    }));
    this.blacklist = new JsonFileStore(path.join(this.dataDir, 'blacklist_words.json'), () => ({
      blacklisted_words: []
    }));
    this.filteredWords = new JsonFileStore(path.join(this.dataDir, 'filtered_words.json'), () => ({
      filtered_messages: []
    }));
    this.bookmarks = new JsonFileStore(this.bookmarksPath, () => ({}));
    this.tokenUsage = new JsonFileStore(path.join(this.dataDir, 'token_usage.json'), () => ({
      entries: []
    }));
  }

  async fileExists(filePath) {
    try {
      await access(filePath);
      return true;
    } catch (error) {
      if (error.code === 'ENOENT') {
        return false;
      }

      throw error;
    }
  }

  async migrateBookmarksIfNeeded() {
    if (this.bookmarksPath === this.legacyBookmarksPath) {
      return;
    }

    if (await this.fileExists(this.bookmarksPath)) {
      return;
    }

    if (!await this.fileExists(this.legacyBookmarksPath)) {
      return;
    }

    await mkdir(path.dirname(this.bookmarksPath), { recursive: true });
    await copyFile(this.legacyBookmarksPath, this.bookmarksPath);
  }

  async ensure() {
    await this.migrateBookmarksIfNeeded();

    await Promise.all([
      this.counting.read(),
      this.aiModeration.read(),
      this.youtube.read(),
      this.chatMessages.read(),
      this.moderationArchive.read(),
      this.blacklist.read(),
      this.filteredWords.read(),
      this.bookmarks.read(),
      this.tokenUsage.read()
    ]);
  }

  getDailySummaryStore(dateString) {
    return new JsonFileStore(path.join(this.summaryDir, `${dateString}.json`), () => ({
      date: dateString,
      message_count: 0,
      summary: '',
      timestamp: new Date().toISOString(),
      topic_message_ids: [],
      auto_generated: false,
      manual: false,
      requested_by: null
    }));
  }

  async listDailySummaryDates() {
    try {
      const { readdir } = await import('node:fs/promises');
      const files = await readdir(this.summaryDir);
      return files
        .filter((fileName) => fileName.endsWith('.json'))
        .map((fileName) => fileName.replace(/\.json$/u, ''))
        .sort();
    } catch (error) {
      if (error.code === 'ENOENT') {
        return [];
      }

      throw error;
    }
  }
}
