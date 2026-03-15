import { PermissionsBitField, type ChatInputCommandInteraction } from "discord.js";

export const hasAdminPermission = (interaction: ChatInputCommandInteraction): boolean =>
  interaction.memberPermissions?.has(PermissionsBitField.Flags.Administrator) ?? false;
