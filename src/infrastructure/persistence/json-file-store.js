import { mkdir, readFile, rename, writeFile } from 'node:fs/promises';
import path from 'node:path';

export class JsonFileStore {
  constructor(filePath, createDefaultValue) {
    this.filePath = filePath;
    this.createDefaultValue = createDefaultValue;
  }

  async read() {
    try {
      const raw = await readFile(this.filePath, 'utf8');
      return JSON.parse(raw);
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }

      const defaultValue = this.createDefaultValue();
      await this.write(defaultValue);
      return defaultValue;
    }
  }

  async write(value) {
    await mkdir(path.dirname(this.filePath), { recursive: true });
    const tempPath = `${this.filePath}.tmp`;
    const serialized = JSON.stringify(value, null, 2);
    await writeFile(tempPath, serialized, 'utf8');
    await rename(tempPath, this.filePath);
    return value;
  }

  async update(mutator) {
    const current = await this.read();
    const next = await mutator(structuredClone(current));
    return this.write(next);
  }
}
