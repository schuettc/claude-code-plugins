import { describe, it, expect, vi } from "vitest";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { buildServer } from "../src/server.js";
import type { GhostClient } from "../src/core/ghost-client.js";

function fakeClient(): GhostClient {
  return {
    baseUrl: "https://x.ghost.io",
    siteInfo: vi.fn(),
    listPosts: vi.fn(),
    getPost: vi.fn(),
    listTags: vi.fn(),
    createPost: vi.fn().mockResolvedValue({
      id: "p1", slug: "hello", url: "https://x.ghost.io/hello/",
      editorUrl: "https://x.ghost.io/ghost/#/editor/post/p1", cardCount: 1,
    }),
    updatePost: vi.fn().mockResolvedValue({
      id: "p1", slug: "hello", url: "https://x.ghost.io/hello/",
      editorUrl: "https://x.ghost.io/ghost/#/editor/post/p1",
    }),
    uploadImage: vi.fn().mockResolvedValue({ url: "https://x/img.jpg" }),
  } as GhostClient;
}

async function connect(client: GhostClient) {
  const server = buildServer(client);
  const [a, b] = InMemoryTransport.createLinkedPair();
  const mcp = new Client({ name: "test", version: "0" });
  await Promise.all([server.connect(a), mcp.connect(b)]);
  return mcp;
}

describe("write tools", () => {
  it("registers all seven tools", async () => {
    const mcp = await connect(fakeClient());
    const names = (await mcp.listTools()).tools.map((t) => t.name).sort();
    expect(names).toEqual([
      "ghost_image_upload", "ghost_post_create", "ghost_post_get",
      "ghost_post_list", "ghost_post_update", "ghost_site_info", "ghost_tag_list",
    ]);
  });

  it("ghost_post_create forwards fields and returns the editor url", async () => {
    const client = fakeClient();
    const mcp = await connect(client);
    const res: any = await mcp.callTool({
      name: "ghost_post_create",
      arguments: { title: "Hello", markdown: "Body.", status: "draft", tags: ["early-access"] },
    });
    expect(client.createPost).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Hello", markdown: "Body.", status: "draft", tags: ["early-access"], type: "post" }),
    );
    expect(res.content[0].text).toContain("editor/post/p1");
  });

  it("ghost_post_update forwards slug + markdown", async () => {
    const client = fakeClient();
    const mcp = await connect(client);
    await mcp.callTool({
      name: "ghost_post_update",
      arguments: { slug: "hello", markdown: "New." },
    });
    expect(client.updatePost).toHaveBeenCalledWith(
      expect.objectContaining({ slug: "hello", markdown: "New.", type: "post" }),
    );
  });

  it("ghost_post_update rejects when neither id nor slug is given", async () => {
    const mcp = await connect(fakeClient());
    const res: any = await mcp.callTool({ name: "ghost_post_update", arguments: { markdown: "x" } });
    expect(res.isError).toBe(true);
  });

  it("ghost_image_upload returns the url", async () => {
    const client = fakeClient();
    const mcp = await connect(client);
    const res: any = await mcp.callTool({
      name: "ghost_image_upload",
      arguments: { path: "/tmp/a.jpg" },
    });
    expect(client.uploadImage).toHaveBeenCalledWith("/tmp/a.jpg");
    expect(res.content[0].text).toContain("img.jpg");
  });
});
