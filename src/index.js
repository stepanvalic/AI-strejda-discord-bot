import { bootstrap } from './app/bootstrap.js';

bootstrap().catch((error) => {
  console.error('Bot spadl při startu:', error);
  process.exitCode = 1;
});
