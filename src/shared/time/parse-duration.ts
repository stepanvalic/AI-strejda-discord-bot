const unitsInMilliseconds: Record<string, number> = {
  s: 1_000,
  m: 60_000,
  h: 3_600_000,
  d: 86_400_000,
  y: 31_536_000_000,
};

export const parseDurationInput = (input?: string): number => {
  if (!input) {
    return 5 * 60_000;
  }

  const normalized = input.trim().toLowerCase();

  if (/^\d+$/.test(normalized)) {
    return Number.parseInt(normalized, 10) * 60_000;
  }

  const matches = [...normalized.matchAll(/(\d+)\s*([smhdy])/g)];
  if (matches.length === 0) {
    throw new Error("Neplatny format casu. Pouzij napr. 15m, 2h nebo 1d12h.");
  }

  const consumed = matches.map((match) => match[0]).join("");
  if (consumed !== normalized.replace(/\s+/g, "")) {
    throw new Error("Neplatny format casu. Pouzij jen kombinace s, m, h, d nebo y.");
  }

  return matches.reduce((total, match) => {
    const amount = Number.parseInt(match[1], 10);
    const unit = match[2];
    return total + amount * unitsInMilliseconds[unit];
  }, 0);
};

export const clampTimeoutDuration = (milliseconds: number): number => {
  const max = 28 * 86_400_000;
  return Math.min(milliseconds, max);
};
