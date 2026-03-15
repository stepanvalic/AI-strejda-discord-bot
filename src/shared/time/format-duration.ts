const parts = [
  { label: "d", size: 86_400_000 },
  { label: "h", size: 3_600_000 },
  { label: "m", size: 60_000 },
  { label: "s", size: 1_000 },
];

export const formatDuration = (milliseconds: number): string => {
  if (milliseconds <= 0) {
    return "0s";
  }

  let remaining = milliseconds;
  const result: string[] = [];

  for (const part of parts) {
    if (remaining < part.size && result.length === 0 && part.label !== "s") {
      continue;
    }

    const value = Math.floor(remaining / part.size);
    remaining -= value * part.size;

    if (value > 0 || (part.label === "s" && result.length === 0)) {
      result.push(`${value}${part.label}`);
    }
  }

  return result.join(" ");
};
