import type { Logger } from "pino";

export class SystemService {
  constructor(private readonly logger: Logger) {}

  scheduleShutdown(delayMs = 1_500): void {
    this.logger.warn({ delayMs }, "Shutdown requested");
    setTimeout(() => process.exit(0), delayMs).unref();
  }
}
