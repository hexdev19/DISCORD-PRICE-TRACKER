const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Sign in with Discord (OAuth2 identify + email). */
export const loginUrl = `${API_BASE_URL}/auth/discord/login`;

/** Add the bot to a Discord server (OAuth2 bot authorization). */
export const inviteUrl = `${API_BASE_URL}/auth/discord/bot`;
