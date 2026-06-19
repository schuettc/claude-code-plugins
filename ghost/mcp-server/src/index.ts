#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { loadConfig, GhostConfigError } from "./config.js";
import { createGhostClient } from "./core/ghost-client.js";
import { buildServer } from "./server.js";

export async function main(env: NodeJS.ProcessEnv = process.env): Promise<void> {
  let config;
  try {
    config = loadConfig(env);
  } catch (e) {
    if (e instanceof GhostConfigError) {
      console.error(`ghost-mcp: ${e.message}`);
      process.exit(1);
    }
    throw e;
  }
  const client = createGhostClient(config);
  const server = buildServer(client);
  await server.connect(new StdioServerTransport());
}

// Run only when invoked directly (not when imported by tests).
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
