import { createApp } from "./app/create-app.js";

const main = async () => {
  const app = await createApp();
  await app.start();
};

main().catch((error) => {
  console.error("Bot bootstrap failed", error);
  process.exitCode = 1;
});
