import { describe, it, expect, vi } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { buildServer } from "../src/server.js";
import type { GhostClient } from "../src/core/ghost-client.js";

function fakeClient(overrides: Partial<GhostClient> = {}): GhostClient {
  return {
    baseUrl: "https://x.ghost.io",
    siteInfo: vi.fn().mockResolvedValue({ title: "Blog", url: "https://x.ghost.io", version: "5.0" }),
    listPosts: vi.fn().mockResolvedValue([{ id: "p1", slug: "hello", title: "Hello" }]),
    getPost: vi.fn().mockResolvedValue({ id: "p1", slug: "hello" }),
    listTags: vi.fn().mockResolvedValue([{ slug: "early-access", name: "Early Access" }]),
    createPost: vi.fn(),
    updatePost: vi.fn(),
    uploadImage: vi.fn(),
    ...overrides,
  } as GhostClient;
}

async function connect(client: GhostClient) {
  const server = buildServer(client);
  const [a, b] = InMemoryTransport.createLinkedPair();
  const mcp = new Client({ name: "test", version: "0" });
  await Promise.all([server.connect(a), mcp.connect(b)]);
  return mcp;
}

describe("read tools", () => {
  it("registers the four read tools (among seven total)", async () => {
    const mcp = await connect(fakeClient());
    const names = (await mcp.listTools()).tools.map((t) => t.name);
    expect(names).toEqual(
      expect.arrayContaining(["ghost_post_get", "ghost_post_list", "ghost_site_info", "ghost_tag_list"]),
    );
    expect(names).toHaveLength(7);
  });

  it("ghost_site_info returns site json", async () => {
    const mcp = await connect(fakeClient());
    const res: any = await mcp.callTool({ name: "ghost_site_info", arguments: {} });
    expect(res.content[0].text).toContain("Blog");
  });

  it("ghost_post_get passes slug through to the client", async () => {
    const client = fakeClient();
    const mcp = await connect(client);
    await mcp.callTool({ name: "ghost_post_get", arguments: { slug: "hello" } });
    expect(client.getPost).toHaveBeenCalledWith({ slug: "hello", id: undefined, type: "post" });
  });

  it("ghost_post_get rejects when neither id nor slug is given", async () => {
    const mcp = await connect(fakeClient());
    const res: any = await mcp.callTool({ name: "ghost_post_get", arguments: {} });
    expect(res.isError).toBe(true);
  });
});
