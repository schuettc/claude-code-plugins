import GhostAdminAPI from "@tryghost/admin-api";
import type { GhostConfig } from "../config.js";
import { buildLexical } from "./lexical-builder.js";
import { stripFrontmatter, stripLeadingH1 } from "./markdown.js";

export type PostType = "post" | "page";

export interface GhostApiLike {
  posts: any;
  pages: any;
  tags: any;
  images: { upload(data: { file: string }): Promise<{ url: string }> };
  site: { read(): Promise<any> };
}

export interface ListParams {
  filter?: string;
  order?: string;
  limit?: number | "all";
  page?: number;
  fields?: string;
  type?: PostType;
}

export interface GetArgs {
  id?: string;
  slug?: string;
  type?: PostType;
}

export interface PostInput {
  id?: string;
  type?: PostType;
  title?: string;
  slug?: string;
  markdown?: string;
  html?: string;
  tags?: string[];
  authors?: string[];
  status?: string;
  visibility?: string;
  published_at?: string;
  feature_image?: string;
  custom_excerpt?: string;
  meta_title?: string;
  meta_description?: string;
}

export interface WriteResult {
  id: string;
  slug: string;
  url: string;
  editorUrl: string;
  cardSummary?: string;
  cardCount?: number;
}

export interface GhostClient {
  baseUrl: string;
  siteInfo(): Promise<any>;
  listPosts(params?: ListParams): Promise<any[]>;
  getPost(args: GetArgs): Promise<any | null>;
  listTags(params?: { filter?: string; limit?: number | "all" }): Promise<any[]>;
  createPost(input: PostInput): Promise<WriteResult>;
  updatePost(input: PostInput): Promise<WriteResult>;
  uploadImage(filePath: string): Promise<{ url: string }>;
}

export function editorUrl(baseUrl: string, id: string): string {
  return `${baseUrl.replace(/\/$/, "")}/ghost/#/editor/post/${id}`;
}

// Build the field payload shared by create + update. Tags are attached
// inline by slug — Ghost auto-creates missing tags and matches existing
// ones by slug, which is also how we avoid duplicate "early-access-2" tags.
function buildPayload(input: PostInput): {
  data: Record<string, unknown>;
  opts: Record<string, unknown>;
  card?: { cardSummary: string; cardCount: number };
} {
  const data: Record<string, unknown> = {};
  for (const key of [
    "title",
    "slug",
    "status",
    "visibility",
    "published_at",
    "feature_image",
    "custom_excerpt",
    "meta_title",
    "meta_description",
  ] as const) {
    if (input[key] !== undefined) data[key] = input[key];
  }
  if (input.tags) data.tags = input.tags.map((slug) => ({ slug }));
  if (input.authors) data.authors = input.authors;

  let opts: Record<string, unknown> = {};
  let card: { cardSummary: string; cardCount: number } | undefined;

  if (input.markdown !== undefined) {
    const prepared = stripLeadingH1(stripFrontmatter(input.markdown));
    const { lexical, cardSummary, cardCount } = buildLexical(prepared);
    data.lexical = lexical;
    card = { cardSummary, cardCount };
  } else if (input.html !== undefined) {
    data.html = input.html;
    opts = { source: "html" };
  }
  return { data, opts, card };
}

function toWriteResult(
  post: { id: string; slug: string; url?: string },
  baseUrl: string,
  card?: { cardSummary: string; cardCount: number },
): WriteResult {
  return {
    id: post.id,
    slug: post.slug,
    url: post.url ?? `${baseUrl.replace(/\/$/, "")}/${post.slug}/`,
    editorUrl: editorUrl(baseUrl, post.id),
    ...(card ?? {}),
  };
}

export function ghostClientFromApi(
  api: GhostApiLike,
  baseUrl: string,
): GhostClient {
  const resource = (type: PostType = "post") =>
    type === "page" ? api.pages : api.posts;

  return {
    baseUrl,

    async siteInfo() {
      return api.site.read();
    },

    async listPosts(params: ListParams = {}) {
      const { type, ...rest } = params;
      const query: Record<string, unknown> = { include: "tags" };
      if (rest.filter !== undefined) query.filter = rest.filter;
      if (rest.order !== undefined) query.order = rest.order;
      if (rest.limit !== undefined) query.limit = rest.limit;
      if (rest.page !== undefined) query.page = rest.page;
      if (rest.fields !== undefined) query.fields = rest.fields;
      return resource(type).browse(query);
    },

    async getPost({ id, slug, type = "post" }: GetArgs) {
      const rows = await resource(type).browse({
        filter: id ? `id:${id}` : `slug:${slug}`,
        limit: 1,
        formats: ["html", "lexical"],
        include: "tags",
      });
      return rows[0] ?? null;
    },

    async listTags(params: { filter?: string; limit?: number | "all" } = {}) {
      return api.tags.browse(params);
    },

    async createPost(input: PostInput) {
      const { data, opts, card } = buildPayload(input);
      const created = await resource(input.type).add(data, opts);
      return toWriteResult(created, baseUrl, card);
    },

    async updatePost(input: PostInput) {
      const existing = await this.getPost({
        id: input.id as string | undefined,
        slug: input.slug,
        type: input.type,
      });
      if (!existing) {
        throw new Error(
          `Post not found for ${input.id ? `id:${input.id}` : `slug:${input.slug}`}`,
        );
      }
      const { data, opts, card } = buildPayload(input);
      data.id = existing.id;
      data.updated_at = existing.updated_at; // optimistic-lock token
      const updated = await resource(input.type).edit(data, opts);
      return toWriteResult(updated, baseUrl, card);
    },

    async uploadImage(filePath: string) {
      return api.images.upload({ file: filePath });
    },
  };
}

export function createGhostClient(config: GhostConfig): GhostClient {
  const api = new GhostAdminAPI({
    url: config.url,
    key: config.adminKey,
    version: "v5.0",
  }) as unknown as GhostApiLike;
  return ghostClientFromApi(api, config.url);
}
