import dotenv from 'dotenv';
import { envSchema } from './schema.js';

export function loadEnv() {
  dotenv.config();
  return envSchema.parse(process.env);
}
