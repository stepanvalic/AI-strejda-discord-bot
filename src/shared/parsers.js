const DURATION_UNITS = new Map([
  ['s', 1000],
  ['m', 60_000],
  ['h', 3_600_000],
  ['d', 86_400_000],
  ['y', 31_536_000_000]
]);

export function parseDurationInput(input) {
  if (!input) {
    return 5 * 60_000;
  }

  const normalized = input.trim().toLowerCase();

  if (/^\d+$/u.test(normalized)) {
    return Number(normalized) * 60_000;
  }

  const regex = /(\d+)([smhdy])/gu;
  let matchedLength = 0;
  let total = 0;

  for (const match of normalized.matchAll(regex)) {
    matchedLength += match[0].length;
    total += Number(match[1]) * DURATION_UNITS.get(match[2]);
  }

  if (!total || matchedLength !== normalized.length) {
    throw new Error('Neplatný formát délky timeoutu.');
  }

  return total;
}
