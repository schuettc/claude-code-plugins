import { describe, it, expect, vi } from "vitest";
import { ghostClientFromApi } from "../src/core/ghost-client.js";

function fakeApi() {
  const made = { id: "p1", slug: "hello", url: "https://x.ghost.io/hello/" };
  const posts = {
    browse: vi.fn().mockResolvedValue([
      { id: "p1", slug: "hello", updated_at: "2026-06-18T00:00:00.000Z" },
    ]),
    read: vi.fn(),
    add: vi.fn().mockResolvedValue(made),
    edit: vi.fn().mockResolvedValue(made),
  };
  return {
    posts,
    pages: { browse: vi.fn(), add: vi.fn(), edit: vi.fn(), read: vi.fn() },
    tags: { browse: vi.fn() },
    images: { upload: vi.fn().mockResolvedValue({ url: "https://x/img.jpg" }) },
    site: { read: vi.fn() },
  };
}

describe("GhostClient writes", () => {
  it("createPost builds lexical and sets status/visibility, returns urls", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    const res = await client.createPost({
      title: "Hello",
      slug: "hello",
      markdown: "Body.",
      status: "draft",
      tags: ["early-access"],
    });
    const [data, opts] = api.posts.add.mock.calls[0];
    expect(data.title).toBe("Hello");
    expect(data.status).toBe("draft");
    expect(typeof data.lexical).toBe("string");
    expect(data.tags).toEqual([{ slug: "early-access" }]);
    expect(opts).toEqual({});
    expect(res).toMatchObject({
      id: "p1",
      slug: "hello",
      editorUrl: "https://x.ghost.io/ghost/#/editor/post/p1",
    });
    expect(res.cardCount).toBe(1);
  });

  it("createPost with html uses source:html and no lexical", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    await client.createPost({ title: "H", html: "<p>x</p>" });
    const [data, opts] = api.posts.add.mock.calls[0];
    expect(data.html).toBe("<p>x</p>");
    expect(data.lexical).toBeUndefined();
    expect(opts).toEqual({ source: "html" });
  });

  it("updatePost resolves slug, read-then-edits with updated_at, strips frontmatter+H1", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    await client.updatePost({
      slug: "hello",
      markdown: "---\ntitle: Hello\n---\n\n# Hello\n\nNew body.",
    });
    expect(api.posts.browse).toHaveBeenCalledWith(
      expect.objectContaining({ filter: "slug:hello" }),
    );
    const [data] = api.posts.edit.mock.calls[0];
    expect(data.id).toBe("p1");
    expect(data.updated_at).toBe("2026-06-18T00:00:00.000Z");
    const cards = JSON.parse(data.lexical).root.children;
    expect(cards[0].markdown).toBe("New body.");
  });

  it("updatePost syncs metadata when provided", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    await client.updatePost({
      slug: "hello",
      title: "New Title",
      tags: ["t1"],
      custom_excerpt: "ex",
    });
    const [data] = api.posts.edit.mock.calls[0];
    expect(data.title).toBe("New Title");
    expect(data.tags).toEqual([{ slug: "t1" }]);
    expect(data.custom_excerpt).toBe("ex");
  });

  it("updatePost throws when the slug is not found", async () => {
    const api = fakeApi();
    api.posts.browse.mockResolvedValue([]);
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    await expect(client.updatePost({ slug: "missing", markdown: "x" })).rejects.toThrow(
      /not found/,
    );
  });

  it("uploadImage returns the url", async () => {
    const api = fakeApi();
    const client = ghostClientFromApi(api, "https://x.ghost.io");
    expect(await client.uploadImage("/tmp/a.jpg")).toEqual({ url: "https://x/img.jpg" });
    expect(api.images.upload).toHaveBeenCalledWith({ file: "/tmp/a.jpg" });
  });
});
