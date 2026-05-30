export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/** Sign in with Discord (OAuth2 identify + email). */
export const loginUrl = `${API_BASE_URL}/auth/discord/login`;

/** Add the bot to a Discord server (OAuth2 bot authorization). */
export const inviteUrl = `${API_BASE_URL}/auth/discord/bot`;

export type Plan = string;

export interface Me {
  id: string;
  discordId: string;
  username: string | null;
  avatar: string | null;
  email: string | null;
  plan: Plan;
}

export interface ServerCard {
  guildId: string;
  name: string | null;
  iconHash: string | null;
  isAdmin: boolean;
  watchCount: number;
}

export interface ServerOverview {
  guildId: string;
  name: string | null;
  iconHash: string | null;
  isAdmin: boolean;
  regionDefault: string | null;
  watchCount: number;
}

export interface AlertRules {
  [key: string]: unknown;
}

export interface WatchRow {
  id: string;
  shortId: string;
  title: string | null;
  imageUrl: string | null;
  domain: string;
  sourceUrl: string;
  currency: string | null;
  lastPrice: number | null;
  inStock: boolean | null;
  isActive: boolean;
  paused: boolean;
  lastScrapedAt: string | null;
  alertRules: AlertRules;
}

export interface WatchProduct {
  title: string | null;
  imageUrl: string | null;
  domain: string;
  sourceUrl: string;
  brand: string | null;
  currency: string | null;
  lastPrice: number | null;
  inStock: boolean | null;
  lastScrapedAt: string | null;
  lastScrapeStatus: string | null;
}

export interface AlertRow {
  id: number;
  ruleType: string;
  triggeredAt: string;
  previousPrice: number | null;
  newPrice: number | null;
  previousInStock: boolean | null;
  newInStock: boolean | null;
  deliveryStatus: string;
}

export interface WatchDetail {
  id: string;
  shortId: string;
  guildId: string;
  product: WatchProduct;
  alertRules: AlertRules;
  isActive: boolean;
  paused: boolean;
  createdAt: string;
  alerts: AlertRow[];
}

export interface SnapshotPoint {
  t: string;
  price: number | null;
  inStock: boolean | null;
}

export interface Snapshots {
  currency: string | null;
  points: SnapshotPoint[];
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message?: string) {
    super(message ?? `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: { Accept: "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new ApiError(res.status, res.statusText);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const getMe = () => apiFetch<Me>("/auth/me");
export const getServers = () => apiFetch<ServerCard[]>("/servers");
export const getServer = (guildId: string) =>
  apiFetch<ServerOverview>(`/servers/${guildId}`);
export const getWatches = (guildId: string) =>
  apiFetch<WatchRow[]>(`/servers/${guildId}/watches`);
export const getWatch = (watchId: string) =>
  apiFetch<WatchDetail>(`/watches/${watchId}`);

export function getSnapshots(
  watchId: string,
  params?: { from?: string; to?: string },
): Promise<Snapshots> {
  const q = new URLSearchParams();
  if (params?.from) q.set("from", params.from);
  if (params?.to) q.set("to", params.to);
  const qs = q.toString();
  return apiFetch<Snapshots>(
    `/watches/${watchId}/snapshots${qs ? `?${qs}` : ""}`,
  );
}

export const logout = () =>
  apiFetch<{ ok: true }>("/auth/logout", { method: "POST" });

export function avatarUrl(me: Pick<Me, "discordId" | "avatar">): string {
  return me.avatar
    ? `https://cdn.discordapp.com/avatars/${me.discordId}/${me.avatar}.png?size=64`
    : "https://cdn.discordapp.com/embed/avatars/0.png";
}

export function serverIconUrl(
  s: Pick<ServerCard, "guildId" | "iconHash">,
): string | null {
  return s.iconHash
    ? `https://cdn.discordapp.com/icons/${s.guildId}/${s.iconHash}.png?size=64`
    : null;
}
