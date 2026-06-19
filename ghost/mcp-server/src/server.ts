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
    async ({ type, id, slug }) => {
      if (!id && !slug) {
        return { isError: true, content: [{ type: "text" as const, text: "Provide id or slug." }] };
      }
      return json(await client.getPost({ type: type as PostType, id, slug }));
    },
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

  const writeFields = {
    type: typeArg,
    title: z.string().optional(),
    slug: z.string().optional(),
    markdown: z.string().optional().describe("Markdown body; built into card-split lexical."),
    html: z.string().optional().describe("HTML body; sent with source:html. Use markdown unless you have raw HTML."),
    tags: z.array(z.string()).optional().describe("Tag slugs; attached inline, auto-created if missing."),
    authors: z.array(z.string()).optional().describe("Author emails or slugs."),
    status: z.enum(["draft", "published", "scheduled"]).optional(),
    visibility: z.enum(["public", "members", "paid"]).optional(),
    published_at: z.string().optional().describe("ISO date; with status=scheduled, schedules the post."),
    feature_image: z.string().optional(),
    custom_excerpt: z.string().optional(),
    meta_title: z.string().optional(),
    meta_description: z.string().optional(),
  };

  server.registerTool(
    "ghost_post_create",
    {
      title: "Create a Ghost post/page",
      description:
        "Create a post or page from Markdown (built into card-split lexical) or HTML. Returns the public and editor URLs.",
      inputSchema: writeFields,
    },
    async (args) => json(await client.createPost({ ...args, type: args.type as PostType })),
  );

  server.registerTool(
    "ghost_post_update",
    {
      title: "Update a Ghost post/page",
      description:
        "Update a post or page in place by id or slug. Read-then-edit (handles updated_at) and syncs title/tags/excerpt/meta, not just the body.",
      inputSchema: { ...writeFields, id: z.string().optional() },
    },
    async (args) => {
      if (!args.id && !args.slug) {
        return { isError: true, content: [{ type: "text" as const, text: "Provide id or slug to identify the post." }] };
      }
      return json(await client.updatePost({ ...args, type: args.type as PostType }));
    },
  );

  server.registerTool(
    "ghost_image_upload",
    {
      title: "Upload an image to Ghost",
      description: "Upload a local image file to Ghost storage and return its CDN url (e.g. for a feature image).",
      inputSchema: { path: z.string().describe("Absolute path to the image file.") },
    },
    async ({ path }) => json(await client.uploadImage(path)),
  );

  return server;
}
