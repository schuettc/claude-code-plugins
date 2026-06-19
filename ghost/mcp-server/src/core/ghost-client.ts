import GhostAdminAPI from "@tryghost/admin-api";
import type { GhostConfig } from "../config.js";

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

export interface GhostClient {
  baseUrl: string;
  siteInfo(): Promise<any>;
  listPosts(params?: ListParams): Promise<any[]>;
  getPost(args: GetArgs): Promise<any | null>;
  listTags(params?: { filter?: string; limit?: number | "all" }): Promise<any[]>;
}

export function editorUrl(baseUrl: string, id: string): string {
  return `${baseUrl.replace(/\/$/, "")}/ghost/#/editor/post/${id}`;
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
