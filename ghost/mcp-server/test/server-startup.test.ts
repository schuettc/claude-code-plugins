// Integration gate: spawn the REAL entry point (src/index.ts) as a child
// process and talk to it over stdio, exactly like an MCP client (Claude) does.
//
// Every other test drives buildServer(fakeClient) directly, so they never
// exercise loadConfig -> createGhostClient -> buildServer -> StdioServer
// Transport -> serve. That left a hole: a server that crashes on startup or
// never completes the stdio handshake would still pass the whole suite. This
// test fails if the process doesn't boot and serve its tools — the "fails out
// of the gate" class of bug.
import { describe, it, expect, afterEach } from "vitest";
import { fileURLToPath } from "node:url";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const ROOT = fileURLToPath(new URL("..", import.meta.url)); // package root

// Valid *format* creds so loadConfig passes. listTools is local (no Ghost call),
// so the test boots the real server fully offline — no network, no live Ghost.
const VALID_ENV = {
  GHOST_API_URL: "https://example.ghost.io",
  GHOST_ADMIN_API_KEY:
    "0123456789abcdef01234567:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
};

const EXPECTED_TOOLS = [
  "ghost_image_upload",
  "ghost_post_create",
  "ghost_post_get",
  "ghost_post_list",
  "ghost_post_update",
  "ghost_site_info",
  "ghost_tag_list",
];

let client: Client | undefined;

afterEach(async () => {
  await client?.close().catch(() => {});
  client = undefined;
});

async function startServer(env: Record<string, string>): Promise<Client> {
  const transport = new StdioClientTransport({
    command: "node",
    args: ["--import", "tsx", "src/index.ts"],
    cwd: ROOT,
    // Replace env entirely (don't inherit the runner's GHOST_* if any).
    env: { PATH: process.env.PATH ?? "", ...env },
    stderr: "pipe",
  });
  const c = new Client({ name: "startup-test", version: "0" });
  await c.connect(transport);
  client = c;
  return c;
}

describe("server startup over stdio (real entry point)", () => {
  it("boots with valid env and serves all 7 tools", async () => {
    const c = await startServer(VALID_ENV);
    const names = (await c.listTools()).tools.map((t) => t.name).sort();
    expect(names).toEqual([...EXPECTED_TOOLS].sort());
  }, 20000);

  it("boots from a creds FILE with NO env creds (bulletproof delivery)", async () => {
    // The exact deployment failure we kept hitting: Claude doesn't pass GHOST_*
    // env into the MCP child. With a creds file the server loads them itself and
    // serves normally — zero dependency on env interpolation / userConfig.
    const file = join(
      mkdtempSync(join(tmpdir(), "ghost-creds-")),
      "ghost.creds.json",
    );
    writeFileSync(
      file,
      JSON.stringify({
        GHOST_API_URL: VALID_ENV.GHOST_API_URL,
        GHOST_ADMIN_API_KEY: VALID_ENV.GHOST_ADMIN_API_KEY,
      }),
    );
    // startServer replaces env entirely, so the child gets NO GHOST_API_URL /
    // GHOST_ADMIN_API_KEY — only the file path.
    const c = await startServer({ GHOST_CREDENTIALS_FILE: file });
    const names = (await c.listTools()).tools.map((t) => t.name).sort();
    expect(names).toEqual([...EXPECTED_TOOLS].sort());
  }, 20000);

  it("responds to a tool call without crashing (ghost_post_get arg-guard)", async () => {
    // Drives a full request/response round-trip through the spawned process.
    // ghost_post_get with neither id nor slug returns isError WITHOUT touching
    // Ghost, so it proves the server handles a real call end-to-end offline.
    const c = await startServer(VALID_ENV);
    const res = await c.callTool({ name: "ghost_post_get", arguments: {} });
    expect((res as { isError?: boolean }).isError).toBe(true);
  }, 20000);

  it("still connects without creds and returns a diagnosable error (not an opaque -32000)", async () => {
    // Regression guard for the exact field failure: a missing-env MCP must NOT
    // hard-exit (which Claude surfaces as an undebuggable "-32000 connection
    // closed"). It connects, lists its tools, and the verify call setup-ghost
    // makes returns a clear, actionable error.
    const c = await startServer({ GHOST_API_URL: "", GHOST_ADMIN_API_KEY: "" });
    const names = (await c.listTools()).tools.map((t) => t.name);
    expect(names).toContain("ghost_site_info");
    const res = (await c.callTool({
      name: "ghost_site_info",
      arguments: {},
    })) as { isError?: boolean; content?: Array<{ text?: string }> };
    expect(res.isError).toBe(true);
    expect(res.content?.[0]?.text ?? "").toMatch(
      /setup-ghost|Ghost credentials/,
    );
  }, 20000);
});
