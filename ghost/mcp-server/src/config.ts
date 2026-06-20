import { readFileSync } from "node:fs";
import { join } from "node:path";

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

interface FileCreds {
  url?: string;
  adminKey?: string;
}

// Read GHOST_API_URL / GHOST_ADMIN_API_KEY from a JSON credentials file. This is
// the bulletproof delivery path: it does NOT depend on Claude passing env into
// the spawned MCP child — which is unreliable (a settings.local.json env block
// reaches Bash but not the MCP; .mcp.json ${VAR} resolves against the session's
// process env and breaks on resume; userConfig needs a fresh session). The
// server loads its own creds straight off disk instead.
//
// Path: GHOST_CREDENTIALS_FILE if set (a non-secret path, safe to put in
// .mcp.json), else <cwd>/.claude/ghost.creds.json — the MCP is spawned with the
// project as cwd, and that file is gitignored. Shape:
//   { "GHOST_API_URL": "https://you.ghost.io", "GHOST_ADMIN_API_KEY": "id:secret" }
function readCredsFile(env: NodeJS.ProcessEnv): FileCreds {
  const path =
    env.GHOST_CREDENTIALS_FILE?.trim() ||
    join(process.cwd(), ".claude", "ghost.creds.json");
  let raw: Record<string, unknown>;
  try {
    raw = JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
  } catch {
    return {}; // absent / unreadable / not JSON — fall through to the error
  }
  const str = (v: unknown): string | undefined =>
    typeof v === "string" ? v.trim() : undefined;
  return { url: str(raw.GHOST_API_URL), adminKey: str(raw.GHOST_ADMIN_API_KEY) };
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): GhostConfig {
  let url = env.GHOST_API_URL?.trim();
  let adminKey = env.GHOST_ADMIN_API_KEY?.trim();

  // Env wins; fall back to the credentials file for whatever is still missing.
  if (!url || !adminKey) {
    const file = readCredsFile(env);
    url ||= file.url;
    adminKey ||= file.adminKey;
  }

  if (!url || !adminKey) {
    throw new GhostConfigError(
      "Missing Ghost credentials. Provide GHOST_API_URL and GHOST_ADMIN_API_KEY " +
        "via env, or as a JSON file at .claude/ghost.creds.json (or the path in " +
        "GHOST_CREDENTIALS_FILE). Run the ghost plugin's setup-ghost skill.",
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
