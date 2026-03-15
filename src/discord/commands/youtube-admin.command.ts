import { createGroupCommand } from "./support/group-command.js";
import { replyPlanned } from "./support/response.js";

export const youtubeAdminCommand = createGroupCommand({
  name: "youtube-admin",
  description: "Admin commandy pro YouTube polling a notifikace.",
  category: "YouTube",
  subcommands: [
    {
      name: "zkontroluj-nejnovejsi",
      description: "Zkontroluje nejnovejsi video nebo stream.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "YouTube check latest", [
          ...context.services.youtube.buildOverviewLines(),
          "Chybi YouTube Data API client a store historie videi.",
        ]);
      },
    },
    {
      name: "refresh-embedy",
      description: "Aktualizuje embedy oznamenych videi.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "YouTube refresh embedy", [
          "Command ma refreshnout metadata a statistiky uz oznamenych videi.",
          "Chybi YouTube store a Discord message mapping.",
          ...context.services.youtube.buildOverviewLines(),
        ]);
      },
    },
    {
      name: "posli-posledni-znovu",
      description: "Posle posledni video znovu do notif kanalu.",
      adminOnly: true,
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "YouTube resend latest", [
          "Command ma nacist posledni video, ulozit ho a znovu poslat notifikaci.",
          "Chybi YouTube API klient a historie oznameni.",
          ...context.services.youtube.buildOverviewLines(),
        ]);
      },
    },
  ],
});
