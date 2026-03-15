import { createGroupCommand } from "./support/group-command.js";
import { replyPlanned } from "./support/response.js";

export const bookmarkCommand = createGroupCommand({
  name: "bookmark",
  description: "Osobni bookmarky na Discord zpravy.",
  category: "Bookmarky",
  subcommands: [
    {
      name: "ulozit",
      description: "Ulozi bookmark podle odkazu na zpravu.",
      configure: (builder) =>
        builder
          .addStringOption((option) =>
            option
              .setName("message-link")
              .setDescription("Discord odkaz na zpravu")
              .setRequired(true),
          )
          .addStringOption((option) =>
            option.setName("poznamka").setDescription("Volitelna poznamka").setRequired(false),
          ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Bookmark ulozit", [
          `Message link: ${interaction.options.getString("message-link", true)}`,
          `Poznamka: ${interaction.options.getString("poznamka") ?? "zadna"}`,
          ...context.services.bookmarks.buildUsageNotes(),
        ], false);
      },
    },
    {
      name: "seznam",
      description: "Vypise bookmarky s DM strankovanim.",
      configure: (builder) =>
        builder.addIntegerOption((option) =>
          option
            .setName("strana")
            .setDescription("Volitelna strana vypisu")
            .setRequired(false)
            .setMinValue(1),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Bookmark seznam", [
          `Strana: ${interaction.options.getInteger("strana") ?? 1}`,
          "Vysledek ma chodit do DM po 5 polozkach.",
          "Chybi bookmark store.",
        ], false);
      },
    },
    {
      name: "smazat",
      description: "Smaze bookmark podle poradi.",
      configure: (builder) =>
        builder.addIntegerOption((option) =>
          option
            .setName("poradi")
            .setDescription("Poradove cislo bookmarku")
            .setRequired(true)
            .setMinValue(1),
        ),
      execute: async (interaction, context) => {
        await replyPlanned(interaction, context, "Bookmark smazat", [
          `Poradi: ${interaction.options.getInteger("poradi", true)}`,
          "Prikaz ma smazat jeden bookmark z osobniho seznamu.",
          "Chybi bookmark store.",
        ], false);
      },
    },
  ],
});
