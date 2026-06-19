#!/usr/bin/env node
import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { loadConfig, GhostConfigError } from "./config.js";
import {
  createGhostClient,
  unconfiguredClient,
  type GhostClient,
} from "./core/ghost-client.js";
import { buildServer } from "./server.js";

// Build the Ghost client from env. If credentials are missing/malformed we do
// NOT exit — we log to stderr and return an "unconfigured" client so the MCP
// server still connects and every tool returns a diagnosable "run setup-ghost"
// error (rather than crashing into an opaque "-32000 connection closed").
export function buildClient(env: NodeJS.ProcessEnv): GhostClient {
  try {
    return createGhostClient(loadConfig(env));
  } catch (e) {
    // Catch BOTH our GhostConfigError and any error from the @tryghost/admin-api
    // constructor (e.g. a malformed key) — either way, never hard-exit. Fall
    // back to a client that reports the problem at tool-call time.
    const message =
      e instanceof GhostConfigError
        ? e.message
        : `Ghost client could not start: ${(e as Error).message}. ` +
          `Run the setup-ghost skill to check GHOST_API_URL / GHOST_ADMIN_API_KEY.`;
    console.error(`ghost-blog-mcp: ${message}`);
    return unconfiguredClient(message);
  }
}

export async function main(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  const client = buildClient(env);
  // Startup diagnostic (stderr → MCP log; never the secret): shows whether creds
  // resolved and for which site, so a misconfig is visible without guessing.
  console.error(
    client.baseUrl
      ? `ghost-blog-mcp: starting — site ${client.baseUrl}`
      : "ghost-blog-mcp: starting UNCONFIGURED — no Ghost credentials; run the setup-ghost skill",
  );
  await buildServer(client).connect(new StdioServerTransport());
}

// Run main() only when this file IS the process entry point — not when a test
// imports buildClient/main. The comparison resolves real paths on BOTH sides:
// under npx or `npm i -g`, the bin is invoked through a .bin symlink, so
// process.argv[1] is the symlink while import.meta.url is the real file. A naive
// `import.meta.url === file://${argv[1]}` compare fails to match there, main()
// never runs, and the server silently exits 0 (the MCP shows as "failed").
// realpathSync collapses every symlink permutation so the comparison holds.
function isEntryPoint(): boolean {
  const argv1 = process.argv[1];
  if (!argv1) return false;
  try {
    return realpathSync(argv1) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}

if (isEntryPoint()) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
