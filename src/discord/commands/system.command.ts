import { createGroupCommand } from "./support/group-command.js";
import { createBaseEmbed, replyWithEmbed } from "./support/response.js";

export const systemCommand = createGroupCommand({
  name: "system",
  description: "Skryte a servisni commandy procesu.",
  category: "System",
  subcommands: [
    {
      name: "shutdown",
      description: "Bezpecne vypne proces bota.",
      adminOnly: true,
      listed: false,
      execute: async (interaction, context) => {
        context.services.system.scheduleShutdown();
        const embed = createBaseEmbed(context, "Shutdown", "Proces se za chvili korektne vypne.");
        await replyWithEmbed(interaction, embed, true);
      },
    },
  ],
});
