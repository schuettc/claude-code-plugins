import { describe, it, expect, vi } from "vitest";
import { ghostClientFromApi } from "../src/core/ghost-client.js";

function fakeApi(overrides: any = {}) {
  const posts = {
    browse: vi.fn().mockResolvedValue([]),
    read: vi.fn().mockResolvedValue({}),
    add: vi.fn(),
    edit: vi.fn(),
  };
  return {
    posts,
    pages: { ...posts, browse: vi.fn().mockResolvedValue([]) },
    tags: { browse: vi.fn().mockResolvedValue([]) },
    images: { upload: vi.fn() },
    site: { read: vi.fn().mockResolvedValue({ title: "T", url: "u", version: "5" }) },
    ...overrides,
  };
}

describe("GhostClient reads", () => {
  it("siteInfo reads the site resource", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    expect(await client.siteInfo()).toEqual({ title: "T", url: "u", version: "5" });
    expect(api.site.read).toHaveBeenCalled();
  });

  it("listPosts forwards filter/order/limit and defaults include=tags", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    await client.listPosts({ filter: "status:draft", order: "updated_at DESC", limit: 5 });
    expect(api.posts.browse).toHaveBeenCalledWith({
      filter: "status:draft",
      order: "updated_at DESC",
      limit: 5,
      include: "tags",
    });
  });

  it("getPost by slug browses with a slug filter and lexical+html formats", async () => {
    const api = fakeApi();
    api.posts.browse.mockResolvedValue([{ id: "p1", slug: "hello" }]);
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    const post = await client.getPost({ slug: "hello" });
    expect(api.posts.browse).toHaveBeenCalledWith({
      filter: "slug:hello",
      limit: 1,
      formats: ["html", "lexical"],
      include: "tags",
    });
    expect(post).toMatchObject({ id: "p1" });
  });

  it("getPost routes type=page to the pages resource", async () => {
    const api = fakeApi();
    api.pages.browse.mockResolvedValue([{ id: "pg1", slug: "about" }]);
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    await client.getPost({ slug: "about", type: "page" });
    expect(api.pages.browse).toHaveBeenCalled();
  });

  it("listTags browses tags", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    await client.listTags({ limit: "all" });
    expect(api.tags.browse).toHaveBeenCalledWith({ limit: "all" });
  });
});
