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
    views: Number(detail.statistics?.viewCount || 0),
    likes: Number(detail.statistics?.likeCount || 0),
    comments: Number(detail.statistics?.commentCount || 0),
    message_id: null,
    channel_message_id: null,
    announced_at: null,
    last_updated: new Date().toISOString(),
    is_live: Boolean(detail.liveStreamingDetails?.actualStartTime && !detail.liveStreamingDetails?.actualEndTime),
    scheduled_start_time: detail.liveStreamingDetails?.scheduledStartTime || null,
    actual_start_time: detail.liveStreamingDetails?.actualStartTime || null
  };
}

export class YoutubeService {
  constructor(context) {
    this.context = context;
  }

  async resolveChannelId(handleOrId) {
    if (!handleOrId) {
      throw new Error('YouTube kanál není nastavený.');
    }

    if (handleOrId.startsWith('UC')) {
      return handleOrId;
    }

    const query = handleOrId.replace(/^@/u, '');
    const response = await fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&type=channel&maxResults=1&q=${encodeURIComponent(query)}&key=${this.context.env.YOUTUBE_API_KEY}`);
    const payload = await response.json();
    const item = payload.items?.[0];

    if (!item?.snippet?.channelId) {
      throw new Error('Nepodařilo se najít YouTube kanál.');
    }

    return item.snippet.channelId;
  }

  async fetchLatestVideo() {
    const config = await this.context.configStore.get();

    if (!this.context.env.YOUTUBE_API_KEY) {
      throw new Error('Chybí YOUTUBE_API_KEY.');
    }

    const channelId = await this.resolveChannelId(config.youtube.channelHandleOrId);
    const searchResponse = await fetch(`https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=${channelId}&maxResults=5&order=date&type=video&key=${this.context.env.YOUTUBE_API_KEY}`);
    const searchPayload = await searchResponse.json();
    const firstItem = searchPayload.items?.[0];

    if (!firstItem?.id?.videoId) {
      throw new Error('Nepodařilo se najít žádné video.');
    }

    const detailResponse = await fetch(`https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails,liveStreamingDetails&id=${firstItem.id.videoId}&key=${this.context.env.YOUTUBE_API_KEY}`);
    const detailPayload = await detailResponse.json();
    const detail = detailPayload.items?.[0];

    if (!detail) {
      throw new Error('Nepodařilo se načíst detail videa.');
    }

    return normalizeVideoRecord(detail);
  }

  buildNotification(video, pingRoleId) {
    const liveLabel = video.is_live
      ? 'Právě běží stream'
      : video.scheduled_start_time
        ? 'Naplánovaný stream'
        : 'Nové video';

    return {
      content: video.scheduled_start_time ? null : (pingRoleId ? `<@&${pingRoleId}>` : '@everyone'),
      embeds: [
        createEmbed({
          title: liveLabel,
          color: video.is_live ? Colors.Red : Colors.Blurple,
          description: `[${video.title}](https://www.youtube.com/watch?v=${video.video_id})`,
          fields: [
            { name: 'Kanal', value: video.channel_title, inline: true },
            { name: 'Views', value: String(video.views), inline: true },
            { name: 'Likes', value: String(video.likes), inline: true }
          ]
        }).setThumbnail(video.thumbnail_url)
      ]
    };
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
    const video = await this.fetchLatestVideo();
    await this.saveVideo(video);
    return this.announceVideo(video, force);
  }

  async refreshAnnouncements() {
    const store = await this.context.database.youtube.read();
    const latest = store.videos.slice(0, 5);
    let updated = 0;

    for (const video of latest) {
      await this.saveVideo({
        ...video,
        last_updated: new Date().toISOString()
      });
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

    return this.announceVideo(latest, true);
  }
}
