import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { GhostClient, PostType } from "./core/ghost-client.js";

const typeArg = z
  .enum(["post", "page"])
  .default("post")
  .describe("Whether to operate on a post or a page.");

function json(value: unknown) {
  return { content: [{ type: "text" as const, text: JSON.stringify(value, null, 2) }] };
}

export function buildServer(client: GhostClient): McpServer {
  const server = new McpServer({ name: "ghost-mcp", version: "0.1.0" });

  server.registerTool(
    "ghost_site_info",
    {
      title: "Ghost site info",
      description:
        "Read the connected Ghost site's title, url and version. Use first to confirm credentials work.",
      inputSchema: {},
    },
    async () => json(await client.siteInfo()),
  );

  server.registerTool(
    "ghost_post_list",
    {
      title: "List Ghost posts/pages",
      description:
        "Browse posts or pages with an NQL filter, order, and limit. Use to find a post by slug, list drafts, or pull a corpus.",
      inputSchema: {
        type: typeArg,
        filter: z.string().optional().describe("NQL filter, e.g. status:published"),
        order: z.string().optional().describe("e.g. published_at DESC"),
        limit: z.union([z.number(), z.literal("all")]).optional(),
        fields: z.string().optional(),
      },
    },
    async ({ type, filter, order, limit, fields }) =>
      json(await client.listPosts({ type: type as PostType, filter, order, limit, fields })),
  );

  server.registerTool(
    "ghost_post_get",
    {
      title: "Get a Ghost post/page",
      description:
        "Read a single post or page by id or slug, including its html and lexical. Use for pull-guard before updating.",
      inputSchema: {
        type: typeArg,
        id: z.string().optional(),
        slug: z.string().optional(),
      },
    },
    async ({ type, id, slug }) =>
      json(await client.getPost({ type: type as PostType, id, slug })),
  );

  server.registerTool(
    "ghost_tag_list",
    {
      title: "List Ghost tags",
      description:
        "Browse tags. Use to find a tag's canonical slug before attaching it to a post.",
      inputSchema: {
        filter: z.string().optional(),
        limit: z.union([z.number(), z.literal("all")]).optional(),
      },
    },
    async ({ filter, limit }) => json(await client.listTags({ filter, limit })),
  );

  return server;
}
