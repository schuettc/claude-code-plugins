export interface GhostConfig {
  url: string;
  adminKey: string;
}

export class GhostConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GhostConfigError";
  }
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): GhostConfig {
  const url = env.GHOST_API_URL?.trim();
  const adminKey = env.GHOST_ADMIN_API_KEY?.trim();

  if (!url || !adminKey) {
    throw new GhostConfigError(
      "Missing Ghost credentials. Set GHOST_API_URL and GHOST_ADMIN_API_KEY " +
        "(run the ghost plugin's setup-ghost skill to configure them).",
    );
  }
  if (!/^https?:\/\//.test(url)) {
    throw new GhostConfigError(
      `GHOST_API_URL must be an http(s) URL, got: ${url}`,
    );
  }
  if (!/^[0-9a-f]{24}:[0-9a-f]{64}$/i.test(adminKey)) {
    throw new GhostConfigError(
      "GHOST_ADMIN_API_KEY must be id:secret form — 24 hex chars, a colon, then " +
        "64 hex chars. Copy the Admin API Key from your Ghost custom integration " +
        "(run the setup-ghost skill).",
    );
  }
  return { url, adminKey };
}
