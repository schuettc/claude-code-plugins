#!/usr/bin/env node
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
  const server = buildServer(buildClient(env));
  await server.connect(new StdioServerTransport());
}

// Run only when invoked directly (not when imported by tests).
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
