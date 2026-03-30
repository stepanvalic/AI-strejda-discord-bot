import { Colors } from 'discord.js';
import { createEmbed } from '../../shared/discord-helpers.js';

function normalizeVideoRecord(detail) {
  return {
    video_id: detail.id,
    title: detail.snippet.title,
    description: detail.snippet.description,
    thumbnail_url: detail.snippet.thumbnails?.maxres?.url || detail.snippet.thumbnails?.high?.url || '',
    published_at: detail.snippet.publishedAt,
    channel_title: detail.snippet.channelTitle,
    duration: detail.contentDetails?.duration || '',
    views: detail.statistics?.viewCount ? Number(detail.statistics.viewCount) : null,
    likes: detail.statistics?.likeCount ? Number(detail.statistics.likeCount) : null,
    comments: detail.statistics?.commentCount ? Number(detail.statistics.commentCount) : null,
    message_id: null,
    channel_message_id: null,
    announced_at: null,
    last_updated: new Date().toISOString(),
    is_live: Boolean(detail.liveStreamingDetails?.actualStartTime && !detail.liveStreamingDetails?.actualEndTime),
    scheduled_start_time: detail.liveStreamingDetails?.scheduledStartTime || null,
    actual_start_time: detail.liveStreamingDetails?.actualStartTime || null
  };
}

function decodeXmlEntities(value) {
  return value
    .replaceAll('&amp;', '&')
    .replaceAll('&lt;', '<')
    .replaceAll('&gt;', '>')
    .replaceAll('&quot;', '"')
    .replaceAll('&#39;', "'");
}

function normalizeFeedVideoRecord(feedVideo) {
  return {
    video_id: feedVideo.videoId,
    title: feedVideo.title,
    description: '',
    thumbnail_url: feedVideo.thumbnailUrl,
    published_at: feedVideo.publishedAt,
    channel_title: feedVideo.author,
    duration: '',
    views: null,
    likes: null,
    comments: null,
    message_id: null,
    channel_message_id: null,
    announced_at: null,
    last_updated: new Date().toISOString(),
    is_live: false,
    scheduled_start_time: null,
    actual_start_time: null
  };
}

function formatMetric(value) {
  if (value === null || value === undefined) {
    return 'nezjištěno';
  }

  return new Intl.NumberFormat('cs-CZ').format(value);
}

function mergeVideoWithFeedData(video, feedRecord) {
  return {
    ...video,
    title: feedRecord.title || video.title,
    thumbnail_url: feedRecord.thumbnail_url || video.thumbnail_url,
    published_at: feedRecord.published_at || video.published_at,
    channel_title: feedRecord.channel_title || video.channel_title,
    last_updated: new Date().toISOString()
  };
}

export class YoutubeService {
  constructor(context) {
    this.context = context;
  }

  normalizeChannelInput(handleOrId) {
    const value = handleOrId.trim();

    if (value.startsWith('UC')) {
      return { type: 'channelId', value };
    }

    try {
      const url = new URL(value);

      if (!/youtube\.com$/u.test(url.hostname) && !/www\.youtube\.com$/u.test(url.hostname)) {
        return { type: 'query', value };
      }

      if (url.pathname.startsWith('/channel/')) {
        const channelId = url.pathname.split('/')[2];
        if (channelId?.startsWith('UC')) {
          return { type: 'channelId', value: channelId };
        }
      }

      if (url.pathname.startsWith('/@')) {
        return { type: 'handleUrl', value: `${url.origin}${url.pathname}` };
      }

      return { type: 'query', value };
    } catch {
      if (value.startsWith('@')) {
        return { type: 'handleUrl', value: `https://www.youtube.com/${value}` };
      }

      return { type: 'query', value };
    }
  }

  async resolveChannelIdFromPage(channelUrl) {
    const response = await fetch(channelUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });

    if (!response.ok) {
      throw new Error(`Nepodařilo se načíst YouTube stránku (${response.status}).`);
    }

    const html = await response.text();
    const patterns = [
      /<link rel="canonical" href="https:\/\/www\.youtube\.com\/channel\/(UC[\w-]{20,})"/u,
      /"externalId":"(UC[\w-]{20,})"/u,
      /"browseId":"(UC[\w-]{20,})"/u,
      /https:\/\/www\.youtube\.com\/channel\/(UC[\w-]{20,})/u
    ];

    for (const pattern of patterns) {
      const match = html.match(pattern);
      if (match?.[1]) {
        return match[1];
      }
    }

    if (!html.includes('youtube.com')) {
      throw new Error('Nepodařilo se vyčíst ID YouTube kanálu ze stránky.');
    }
    
    throw new Error('Nepodařilo se vyčíst ID YouTube kanálu ze stránky.');
  }

  async fetchLatestVideoFromFeed(channelId) {
    const response = await fetch(`https://www.youtube.com/feeds/videos.xml?channel_id=${channelId}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });

    if (!response.ok) {
      throw new Error(`Nepodařilo se načíst YouTube feed (${response.status}).`);
    }

    const xml = await response.text();
    const entryMatch = xml.match(/<entry>([\s\S]*?)<\/entry>/u);

    if (!entryMatch?.[1]) {
      throw new Error('V YouTube feedu není žádné video.');
    }

    const entry = entryMatch[1];
    const videoId = entry.match(/<yt:videoId>([^<]+)<\/yt:videoId>/u)?.[1];
    const title = decodeXmlEntities(entry.match(/<title>([^<]+)<\/title>/u)?.[1] ?? '');
    const author = decodeXmlEntities(entry.match(/<name>([^<]+)<\/name>/u)?.[1] ?? '');
    const publishedAt = entry.match(/<published>([^<]+)<\/published>/u)?.[1] ?? new Date().toISOString();
    const thumbnailUrl = entry.match(/<media:thumbnail url="([^"]+)"/u)?.[1] ?? '';

    if (!videoId || !title) {
      throw new Error('V YouTube feedu chybí data o posledním videu.');
    }

    return {
      videoId,
      title,
      author,
      publishedAt,
      thumbnailUrl
    };
  }

  async fetchLatestFeedRecord() {
    const config = await this.context.configStore.get();
    const channelId = await this.resolveChannelId(config.youtube.channelHandleOrId);
    const feedVideo = await this.fetchLatestVideoFromFeed(channelId);
    return normalizeFeedVideoRecord(feedVideo);
  }

  async fetchVideoDetail(videoId) {
    if (!this.context.env.YOUTUBE_API_KEY) {
      return null;
    }

    const detailResponse = await fetch(`https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails,liveStreamingDetails&id=${videoId}&key=${this.context.env.YOUTUBE_API_KEY}`);

    if (!detailResponse.ok) {
      const payload = await detailResponse.json().catch(() => ({}));
      throw new Error(payload.error?.message || `YouTube detail API vrátila ${detailResponse.status}.`);
    }

    const detailPayload = await detailResponse.json();
    return detailPayload.items?.[0] ?? null;
  }

  async fetchVideoMetricsFromPage(videoId) {
    const response = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    });

    if (!response.ok) {
      throw new Error(`Nepodařilo se načíst stránku videa (${response.status}).`);
    }

    const html = await response.text();
    const views = html.match(/"viewCount":"(\d+)"/u)?.[1];
    const likes = html.match(/"likeCountIfLikedNumber":"(\d+)"/u)?.[1];
    const comments = html.match(/"commentCount":"(\d+)"/u)?.[1];

    return {
      views: views ? Number(views) : null,
      likes: likes ? Number(likes) : null,
      comments: comments ? Number(comments) : null
    };
  }

  async resolveChannelId(handleOrId) {
    if (!handleOrId) {
      throw new Error('YouTube kanál není nastavený.');
    }

    const normalized = this.normalizeChannelInput(handleOrId);

    if (normalized.type === 'channelId') {
      return normalized.value;
    }

    if (normalized.type === 'handleUrl') {
      return this.resolveChannelIdFromPage(normalized.value);
    }

    const query = normalized.value.replace(/^@/u, '');
    const response = await fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&maxResults=1&q=${encodeURIComponent(query)}&key=${this.context.env.YOUTUBE_API_KEY}`);
    const payload = await response.json();
    const item = payload.items?.[0];

    if (!item?.snippet?.channelId) {
      throw new Error('Nepodařilo se najít YouTube kanál.');
    }

    return item.snippet.channelId;
  }

  async fetchLatestVideo() {
    return this.enrichVideoMetadata(await this.fetchLatestFeedRecord());
  }

  async enrichVideoMetadata(video) {
    try {
      const detail = await this.fetchVideoDetail(video.video_id);
      if (detail) {
      return {
        ...video,
        ...normalizeVideoRecord(detail),
        message_id: video.message_id ?? null,
        channel_message_id: video.channel_message_id ?? null,
        announced_at: video.announced_at ?? null
      };
      }
    } catch (error) {
      this.context.logger.warn({ err: error }, 'YouTube detail API selhala při obohacení videa.');
    }

    try {
      const metrics = await this.fetchVideoMetricsFromPage(video.video_id);
      return {
        ...video,
        views: metrics.views ?? video.views ?? null,
        likes: metrics.likes ?? video.likes ?? null,
        comments: metrics.comments ?? video.comments ?? null,
        last_updated: new Date().toISOString()
      };
    } catch (error) {
      this.context.logger.warn({ err: error }, 'YouTube stránka videa selhala při obohacení videa.');
      return {
        ...video,
        last_updated: new Date().toISOString()
      };
    }
  }

  buildNotificationEmbed(video) {
    return createEmbed({
      title: video.is_live
        ? 'Právě běží stream'
        : video.scheduled_start_time
          ? 'Naplánovaný stream'
          : 'Nové video',
      color: video.is_live ? Colors.Red : Colors.Blurple,
      description: `[${video.title}](https://www.youtube.com/watch?v=${video.video_id})`,
      fields: [
        { name: 'Kanál', value: video.channel_title, inline: true },
        { name: 'Zhlédnutí', value: formatMetric(video.views), inline: true },
        { name: 'Lajky', value: formatMetric(video.likes), inline: true },
        { name: 'Komentáře', value: formatMetric(video.comments), inline: true }
      ]
    });
  }

  buildNotification(video, pingRoleId) {
    return {
      content: video.scheduled_start_time ? null : (pingRoleId ? `<@&${pingRoleId}>` : '@everyone'),
      embeds: [this.buildNotificationEmbed(video).setImage(video.thumbnail_url)]
    };
  }

  async enrichVideoStats(video) {
    const now = new Date().toISOString();

    try {
      const metrics = await this.fetchVideoMetricsFromPage(video.video_id);

      return {
        ...video,
        views: metrics.views ?? video.views ?? null,
        likes: metrics.likes ?? video.likes ?? null,
        comments: metrics.comments ?? video.comments ?? null,
        last_updated: now
      };
    } catch (error) {
      this.context.logger.warn({ err: error }, 'YouTube stránka videa selhala při aktualizaci metrik.');
      return {
        ...video,
        last_updated: now
      };
    }
  }

  async updateAnnouncementMessage(video) {
    const guild = this.context.client.guilds.cache.get(this.context.guildId);

    if (!guild || !video.channel_message_id || !video.message_id) {
      return false;
    }

    const channel = guild.channels.cache.get(video.channel_message_id) ?? await guild.channels.fetch(video.channel_message_id).catch(() => null);
    if (!channel?.isTextBased?.()) {
      return false;
    }

    const message = await channel.messages.fetch(video.message_id).catch(() => null);
    if (!message) {
      return false;
    }

    await message.edit({
      embeds: [this.buildNotificationEmbed(video).setImage(video.thumbnail_url)]
    });

    return true;
  }

  async refreshRecentVideos(limit = 10) {
    const store = await this.context.database.youtube.read();
    const tracked = store.videos
      .filter((video) => video.message_id && video.channel_message_id)
      .slice(0, limit);

    let updated = 0;

    for (const video of tracked) {
      const enriched = await this.enrichVideoStats(video);
      await this.saveVideo(enriched);
      await this.updateAnnouncementMessage(enriched);
      updated += 1;
    }

    return updated;
  }

  async saveVideo(video) {
    await this.context.database.youtube.update((store) => {
      const existingIndex = store.videos.findIndex((entry) => entry.video_id === video.video_id);

      if (existingIndex === -1) {
        store.videos.unshift(video);
      } else {
        store.videos[existingIndex] = { ...store.videos[existingIndex], ...video };
      }

      return store;
    });
  }

  async announceVideo(video, force = false) {
    const config = await this.context.configStore.get();
    const guild = this.context.client.guilds.cache.get(this.context.guildId);
    const channel = guild.channels.cache.get(config.youtube.notificationChannelId) ?? await guild.channels.fetch(config.youtube.notificationChannelId).catch(() => null);

    if (!channel?.isTextBased?.()) {
      throw new Error('YouTube notifikační kanál není nastavený.');
    }

    const store = await this.context.database.youtube.read();
    const existing = store.videos.find((entry) => entry.video_id === video.video_id);

    if (existing?.message_id && !force) {
      return existing;
    }

    const payload = this.buildNotification(video, config.youtube.pingRoleId);
    const message = await channel.send(payload);
    const enriched = {
      ...video,
      message_id: message.id,
      channel_message_id: channel.id,
      announced_at: new Date().toISOString(),
      last_updated: new Date().toISOString()
    };
    await this.saveVideo(enriched);
    return enriched;
  }

  async checkLatestAndAnnounce({ force = false } = {}) {
    const feedRecord = await this.fetchLatestFeedRecord();
    const store = await this.context.database.youtube.read();
    const existing = store.videos.find((entry) => entry.video_id === feedRecord.video_id);
    const baseVideo = existing ? mergeVideoWithFeedData(existing, feedRecord) : feedRecord;

    await this.saveVideo(baseVideo);

    if (existing?.message_id && !force) {
      return baseVideo;
    }

    const video = await this.enrichVideoMetadata(baseVideo);
    await this.saveVideo(video);
    return this.announceVideo(video, force);
  }

  async refreshAnnouncements() {
    const store = await this.context.database.youtube.read();
    const latest = store.videos.slice(0, 5);
    let updated = 0;

    for (const video of latest) {
      await this.saveVideo(await this.enrichVideoMetadata(video));
      updated += 1;
    }

    return updated;
  }

  async resendLastVideo() {
    const store = await this.context.database.youtube.read();
    const latest = store.videos[0];

    if (!latest) {
      throw new Error('Ve store ještě není žádné video.');
    }

    const enriched = await this.enrichVideoMetadata(latest);
    await this.saveVideo(enriched);
    return this.announceVideo(enriched, true);
  }
}
