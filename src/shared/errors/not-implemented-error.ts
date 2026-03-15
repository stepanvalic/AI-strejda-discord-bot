export class NotImplementedError extends Error {
  constructor(feature: string) {
    super(`${feature} jeste neni dopojene na perzistenci nebo externi integraci.`);
    this.name = "NotImplementedError";
  }
}
