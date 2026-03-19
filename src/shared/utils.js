import path from 'node:path';

export function mergeDeep(baseValue, overrideValue) {
  if (Array.isArray(baseValue)) {
    return Array.isArray(overrideValue) ? [...overrideValue] : [...baseValue];
  }

  if (isPlainObject(baseValue)) {
    const output = { ...baseValue };

    if (!isPlainObject(overrideValue)) {
      return output;
    }

    for (const [key, value] of Object.entries(overrideValue)) {
      output[key] = key in baseValue ? mergeDeep(baseValue[key], value) : structuredClone(value);
    }

    return output;
  }

  return overrideValue === undefined ? structuredClone(baseValue) : overrideValue;
}

export function isPlainObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function chunkArray(items, size) {
  const chunks = [];

  for (let index = 0; index < items.length; index += size) {
    chunks.push(items.slice(index, index + size));
  }

  return chunks;
}

export function chunkText(text, size = 1800) {
  if (!text) {
    return [''];
  }

  const chunks = [];
  let remaining = text;

  while (remaining.length > size) {
    const splitIndex = remaining.lastIndexOf('\n', size);
    const safeIndex = splitIndex > 200 ? splitIndex : size;
    chunks.push(remaining.slice(0, safeIndex));
    remaining = remaining.slice(safeIndex).trimStart();
  }

  chunks.push(remaining);
  return chunks;
}

export function formatDuration(milliseconds) {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const parts = [];

  if (days) {
    parts.push(`${days}d`);
  }

  if (hours || parts.length) {
    parts.push(`${hours}h`);
  }

  if (minutes || parts.length) {
    parts.push(`${minutes}m`);
  }

  parts.push(`${seconds}s`);
  return parts.join(' ');
}

export function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function uniqueStrings(values) {
  return [...new Set(values.filter(Boolean))];
}

export function toDiscordTimestamp(dateLike, style = 'f') {
  const date = dateLike instanceof Date ? dateLike : new Date(dateLike);
  return `<t:${Math.floor(date.getTime() / 1000)}:${style}>`;
}

export function mentionChannel(channelId) {
  return channelId ? `<#${channelId}>` : 'nenastaveno';
}

export function mentionRole(roleId) {
  return roleId ? `<@&${roleId}>` : 'nenastaveno';
}

export function mentionUser(userId) {
  return userId ? `<@${userId}>` : 'neznámý uživatel';
}

export function ensureAbsolute(basePath, targetPath) {
  return path.isAbsolute(targetPath) ? targetPath : path.resolve(basePath, targetPath);
}

export function getDatePartsInTimeZone(date, timeZone) {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });

  const parts = Object.fromEntries(formatter.formatToParts(date).map((part) => [part.type, part.value]));

  return {
    year: Number(parts.year),
    month: Number(parts.month),
    day: Number(parts.day),
    hour: Number(parts.hour),
    minute: Number(parts.minute),
    second: Number(parts.second)
  };
}

export function formatDateInTimeZone(date, timeZone) {
  const parts = getDatePartsInTimeZone(date, timeZone);
  return `${parts.year.toString().padStart(4, '0')}-${parts.month.toString().padStart(2, '0')}-${parts.day.toString().padStart(2, '0')}`;
}

export function getYesterdayDateString(timeZone) {
  const now = new Date();
  const yesterday = new Date(now.getTime() - 86400000);
  return formatDateInTimeZone(yesterday, timeZone);
}

export function truncate(value, maxLength = 1024) {
  if (!value || value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 3)}...`;
}

export function resolveGuildId(envGuildId, configGuildId) {
  return envGuildId || configGuildId || '';
}
