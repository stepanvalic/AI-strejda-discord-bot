import path from 'node:path';
import { JsonFileStore } from '../infrastructure/persistence/json-file-store.js';
import { mergeDeep } from '../shared/utils.js';
import { defaultRuntimeConfig } from './default-runtime-config.js';
import { runtimeConfigSchema } from './schema.js';

export class ConfigStore {
  constructor(filePath) {
    this.filePath = path.resolve(filePath);
    this.store = new JsonFileStore(this.filePath, () => structuredClone(defaultRuntimeConfig));
  }

  async get() {
    const raw = await this.store.read();
    return runtimeConfigSchema.parse(mergeDeep(defaultRuntimeConfig, raw));
  }

  async update(mutator) {
    return this.store.update((current) => {
      const merged = runtimeConfigSchema.parse(mergeDeep(defaultRuntimeConfig, current));
      const nextValue = mutator(merged);
      return runtimeConfigSchema.parse(mergeDeep(defaultRuntimeConfig, nextValue));
    });
  }
}
