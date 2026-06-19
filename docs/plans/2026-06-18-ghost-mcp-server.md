# Ghost MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ghost-mcp`, a local stdio MCP server that exposes the Ghost Admin API to Claude Code as seven deterministic tools, with the writing-workflow ergonomics baked into the write tools.

**Architecture:** Pure, unit-tested core modules (`config`, `markdown`, `lexical-builder`, `ghost-client`) wrapped by thin MCP tool registrations. The server reads the Ghost Admin key from env, talks to Ghost via `@tryghost/admin-api`, and speaks MCP over stdio. Tools inject a `GhostClient` so they're testable without a live Ghost. Published to npm; consumed by the plugin's `.mcp.json` via `npx -y ghost-mcp@latest`.

**Tech Stack:** TypeScript (ESM), `@modelcontextprotocol/sdk`, `@tryghost/admin-api`, `zod` (tool input schemas), `vitest` (tests), `tsx` (dev run), `tsc` (build to `dist/`).

## Global Constraints

- Package name: `ghost-mcp`. Lives at `ghost/mcp-server/` in the repo, published to npm.
- Runtime deps limited to `@modelcontextprotocol/sdk`, `@tryghost/admin-api`, `zod`. No `node-fetch` (use global `fetch`), no `dotenv` (env via `.mcp.json` passthrough).
- Node ≥ 20. ESM only (`"type": "module"`); relative imports use the `.js` extension in source.
- Ghost Admin API version pinned to `v5.0`.
- Credentials come only from env: `GHOST_API_URL`, `GHOST_ADMIN_API_KEY` (`id:secret` hex). Never read from files, never logged.
- Posts and pages are one tool family unified by a `type: 'post' | 'page'` param (default `post`).
- Write tools always accept Markdown and build card-split lexical; `source: 'html'` is the fallback for HTML input.
- v1 tool set is exactly seven: `ghost_site_info`, `ghost_post_list`, `ghost_post_get`, `ghost_post_create`, `ghost_post_update`, `ghost_tag_list`, `ghost_image_upload`. No delete, no publish/schedule policy enforcement (the tool exposes `status`; policy lives in skills).

---

### Task 1: Package scaffold + config module

**Files:**
- Create: `ghost/mcp-server/package.json`
- Create: `ghost/mcp-server/tsconfig.json`
- Create: `ghost/mcp-server/vitest.config.ts`
- Create: `ghost/mcp-server/src/types/ghost-admin-api.d.ts`
- Create: `ghost/mcp-server/src/config.ts`
- Test: `ghost/mcp-server/test/config.test.ts`

**Interfaces:**
- Produces: `GhostConfig = { url: string; adminKey: string }`, `class GhostConfigError extends Error`, `loadConfig(env?: NodeJS.ProcessEnv): GhostConfig`.

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "ghost-mcp",
  "version": "0.1.0",
  "description": "MCP server for the Ghost Admin API",
  "type": "module",
  "bin": { "ghost-mcp": "dist/index.js" },
  "files": ["dist"],
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "typecheck": "tsc --noEmit",
    "dev": "tsx src/index.ts"
  },
  "engines": { "node": ">=20" },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "@tryghost/admin-api": "^1.13.10",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "tsx": "^4.19.0",
    "typescript": "^5.7.0",
    "vitest": "^2.1.0"
  },
  "license": "MIT"
}
```

- [ ] **Step 2: Create `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": false,
    "resolveJsonModule": true
  },
  "include": ["src"],
  "exclude": ["test", "dist"]
}
```

- [ ] **Step 3: Create `vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: { include: ["test/**/*.test.ts"], environment: "node" },
});
```

- [ ] **Step 4: Create a minimal type declaration for `@tryghost/admin-api`**

`@tryghost/admin-api` ships no types. Declare just what we use, in `src/types/ghost-admin-api.d.ts`:

```ts
declare module "@tryghost/admin-api" {
  interface BrowseParams {
    limit?: number | "all";
    page?: number;
    filter?: string;
    order?: string;
    include?: string;
    fields?: string;
    formats?: string[];
  }
  interface Resource {
    browse(params?: BrowseParams): Promise<any[]>;
    read(data: Record<string, any>, options?: Record<string, any>): Promise<any>;
    add(data: Record<string, any>, options?: Record<string, any>): Promise<any>;
    edit(data: Record<string, any>, options?: Record<string, any>): Promise<any>;
  }
  interface Images {
    upload(data: { file: string; ref?: string }): Promise<{ url: string }>;
  }
  interface Site {
    read(): Promise<{ title: string; url: string; version: string }>;
  }
  export default class GhostAdminAPI {
    constructor(options: { url: string; key: string; version: string });
    posts: Resource;
    pages: Resource;
    tags: Resource;
    images: Images;
    site: Site;
  }
}
```

- [ ] **Step 5: Install dependencies**

Run: `cd ghost/mcp-server && npm install`
Expected: `node_modules/` created, no peer-dep errors.

- [ ] **Step 6: Write the failing test for `loadConfig`**

`test/config.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { loadConfig, GhostConfigError } from "../src/config.js";

const VALID = {
  GHOST_API_URL: "https://example.ghost.io",
  GHOST_ADMIN_API_KEY: "64ab12cd34ef:0011223344556677889900aabbccddee",
};

describe("loadConfig", () => {
  it("returns config from valid env", () => {
    expect(loadConfig(VALID)).toEqual({
      url: "https://example.ghost.io",
      adminKey: "64ab12cd34ef:0011223344556677889900aabbccddee",
    });
  });

  it("throws GhostConfigError naming setup-ghost when the key is missing", () => {
    expect(() => loadConfig({ GHOST_API_URL: VALID.GHOST_API_URL })).toThrow(
      GhostConfigError,
    );
    expect(() => loadConfig({ GHOST_API_URL: VALID.GHOST_API_URL })).toThrow(
      /setup-ghost/,
    );
  });

  it("throws on a non-http url", () => {
    expect(() =>
      loadConfig({ ...VALID, GHOST_API_URL: "example.ghost.io" }),
    ).toThrow(GhostConfigError);
  });

  it("throws on a malformed admin key", () => {
    expect(() =>
      loadConfig({ ...VALID, GHOST_ADMIN_API_KEY: "not-a-key" }),
    ).toThrow(GhostConfigError);
  });
});
```

- [ ] **Step 7: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/config.test.ts`
Expected: FAIL — cannot find module `../src/config.js`.

- [ ] **Step 8: Implement `src/config.ts`**

```ts
export interface GhostConfig {
  url: string;
  adminKey: string;
}

export class GhostConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GhostConfigError";
  }
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): GhostConfig {
  const url = env.GHOST_API_URL?.trim();
  const adminKey = env.GHOST_ADMIN_API_KEY?.trim();

  if (!url || !adminKey) {
    throw new GhostConfigError(
      "Missing Ghost credentials. Set GHOST_API_URL and GHOST_ADMIN_API_KEY " +
        "(run the ghost plugin's setup-ghost skill to configure them).",
    );
  }
  if (!/^https?:\/\//.test(url)) {
    throw new GhostConfigError(
      `GHOST_API_URL must be an http(s) URL, got: ${url}`,
    );
  }
  if (!/^[0-9a-f]+:[0-9a-f]+$/i.test(adminKey)) {
    throw new GhostConfigError(
      "GHOST_ADMIN_API_KEY must be in id:secret hex form (copy the Admin API " +
        "Key from your Ghost custom integration).",
    );
  }
  return { url, adminKey };
}
```

- [ ] **Step 9: Run tests and typecheck**

Run: `cd ghost/mcp-server && npx vitest run test/config.test.ts && npm run typecheck`
Expected: PASS (4 tests); typecheck clean.

- [ ] **Step 10: Commit**

```bash
git add ghost/mcp-server
git commit -m "feat(ghost-mcp): scaffold package + config env validation"
```

---

### Task 2: Markdown prep helpers

**Files:**
- Create: `ghost/mcp-server/src/core/markdown.ts`
- Test: `ghost/mcp-server/test/markdown.test.ts`

**Interfaces:**
- Produces: `stripFrontmatter(md: string): string`, `stripLeadingH1(md: string): string`.

- [ ] **Step 1: Write the failing test**

`test/markdown.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { stripFrontmatter, stripLeadingH1 } from "../src/core/markdown.js";

describe("stripFrontmatter", () => {
  it("removes a leading YAML frontmatter block", () => {
    const md = "---\ntitle: Hi\nslug: hi\n---\n\nBody text.";
    expect(stripFrontmatter(md)).toBe("Body text.");
  });

  it("leaves content without frontmatter untouched", () => {
    expect(stripFrontmatter("# Title\n\nBody.")).toBe("# Title\n\nBody.");
  });
});

describe("stripLeadingH1", () => {
  it("removes a leading H1 line", () => {
    expect(stripLeadingH1("# Title\n\nBody.")).toBe("Body.");
  });

  it("does not remove an H2 or mid-document H1", () => {
    expect(stripLeadingH1("## Sub\n\nBody.")).toBe("## Sub\n\nBody.");
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/markdown.test.ts`
Expected: FAIL — cannot find module `../src/core/markdown.js`.

- [ ] **Step 3: Implement `src/core/markdown.ts`**

```ts
// Strip a leading YAML frontmatter block (--- ... ---) if present.
export function stripFrontmatter(md: string): string {
  return md.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n+/, "");
}

// Strip a leading H1 line — Ghost owns the title, so an H1 in the body
// would render as duplicate literal text.
export function stripLeadingH1(md: string): string {
  return md.replace(/^# .+\r?\n\r?\n?/, "");
}
```

- [ ] **Step 4: Run tests**

Run: `cd ghost/mcp-server && npx vitest run test/markdown.test.ts`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add ghost/mcp-server/src/core/markdown.ts ghost/mcp-server/test/markdown.test.ts
git commit -m "feat(ghost-mcp): markdown frontmatter + H1 strip helpers"
```

---

### Task 3: Lexical builder (card splitting)

**Files:**
- Create: `ghost/mcp-server/src/core/lexical-builder.ts`
- Test: `ghost/mcp-server/test/lexical-builder.test.ts`

**Interfaces:**
- Produces: `LexicalResult = { lexical: string; cardSummary: string; cardCount: number }`, `buildLexical(markdown: string): LexicalResult`.

- [ ] **Step 1: Write the failing test**

`test/lexical-builder.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { buildLexical } from "../src/core/lexical-builder.js";

function children(r: { lexical: string }) {
  return JSON.parse(r.lexical).root.children as Array<{ type: string }>;
}

describe("buildLexical", () => {
  it("wraps a tableless post as a single markdown card", () => {
    const r = buildLexical("Just some prose.\n\nMore prose.");
    expect(r.cardCount).toBe(1);
    expect(r.cardSummary).toBe("markdown");
    expect(children(r)[0]).toMatchObject({ type: "markdown", version: 1 });
  });

  it("splits a top-level <table> into its own html card", () => {
    const md = "Intro.\n\n<table><tr><td>x</td></tr></table>\n\nOutro.";
    const r = buildLexical(md);
    expect(r.cardSummary).toBe("markdown, html, markdown");
    expect(r.cardCount).toBe(3);
  });

  it("splits prose on <!-- card --> markers", () => {
    const r = buildLexical("First.\n\n<!-- card -->\n\nSecond.");
    expect(r.cardCount).toBe(2);
    expect(r.cardSummary).toBe("markdown, markdown");
  });

  it("drops empty parts", () => {
    const r = buildLexical("<!-- card -->\n\nOnly one.");
    expect(r.cardCount).toBe(1);
  });

  it("produces a valid lexical root envelope", () => {
    const root = JSON.parse(buildLexical("Hi.").lexical).root;
    expect(root).toMatchObject({ type: "root", version: 1, indent: 0 });
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/lexical-builder.test.ts`
Expected: FAIL — cannot find module `../src/core/lexical-builder.js`.

- [ ] **Step 3: Implement `src/core/lexical-builder.ts`**

```ts
export interface LexicalResult {
  lexical: string;
  cardSummary: string;
  cardCount: number;
}

interface Part {
  type: "markdown" | "html";
  content: string;
}

const TABLE_RE = /<table[\s\S]*?<\/table>/g;
const CARD_MARKER = "<!-- card -->";

// Split markdown into Ghost lexical cards. Top-level <table> blocks become
// their own `html` cards (preserving inline styling and keeping each prose
// chunk between tables independently editable in the Ghost UI); the prose
// between them is further split on explicit <!-- card --> markers. Without
// either boundary, the whole post is one markdown card.
export function buildLexical(markdown: string): LexicalResult {
  const parts: Part[] = [];
  let lastIndex = 0;
  let m: RegExpExecArray | null;
  TABLE_RE.lastIndex = 0;

  while ((m = TABLE_RE.exec(markdown)) !== null) {
    pushMarkdownParts(parts, markdown.slice(lastIndex, m.index));
    parts.push({ type: "html", content: m[0] });
    lastIndex = m.index + m[0].length;
  }
  pushMarkdownParts(parts, markdown.slice(lastIndex));

  const children = parts
    .filter((p) => p.content.trim().length > 0)
    .map((p) =>
      p.type === "markdown"
        ? { type: "markdown", version: 1, markdown: p.content.trim() }
        : { type: "html", version: 1, html: p.content.trim() },
    );

  const lexical = JSON.stringify({
    root: {
      children,
      direction: null,
      format: "",
      indent: 0,
      type: "root",
      version: 1,
    },
  });

  return {
    lexical,
    cardSummary: children.map((c) => c.type).join(", "),
    cardCount: children.length,
  };
}

function pushMarkdownParts(parts: Part[], chunk: string): void {
  if (!chunk) return;
  for (const piece of chunk.split(CARD_MARKER)) {
    parts.push({ type: "markdown", content: piece });
  }
}
```

- [ ] **Step 4: Run tests**

Run: `cd ghost/mcp-server && npx vitest run test/lexical-builder.test.ts`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add ghost/mcp-server/src/core/lexical-builder.ts ghost/mcp-server/test/lexical-builder.test.ts
git commit -m "feat(ghost-mcp): markdown to card-split lexical builder"
```

---

### Task 4: Ghost client — read operations

**Files:**
- Create: `ghost/mcp-server/src/core/ghost-client.ts`
- Test: `ghost/mcp-server/test/ghost-client-read.test.ts`

**Interfaces:**
- Consumes: `GhostConfig` (Task 1).
- Produces:
  - `type PostType = "post" | "page"`
  - `interface GhostApiLike` — the subset of `@tryghost/admin-api` used (`posts`, `pages`, `tags`, `images`, `site`), so tests can pass a fake.
  - `interface GhostClient` with read methods: `siteInfo()`, `listPosts(params)`, `getPost(args)`, `listTags(params)` (write methods added in Task 5).
  - `ghostClientFromApi(api: GhostApiLike, baseUrl: string): GhostClient` (testable).
  - `createGhostClient(config: GhostConfig): GhostClient` (real; builds the API).
  - `editorUrl(baseUrl, id)` helper.

- [ ] **Step 1: Write the failing test (reads)**

`test/ghost-client-read.test.ts`:

```ts
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/ghost-client-read.test.ts`
Expected: FAIL — cannot find module `../src/core/ghost-client.js`.

- [ ] **Step 3: Implement the read half of `src/core/ghost-client.ts`**

```ts
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
```

- [ ] **Step 4: Run tests and typecheck**

Run: `cd ghost/mcp-server && npx vitest run test/ghost-client-read.test.ts && npm run typecheck`
Expected: PASS (5 tests); typecheck clean.

- [ ] **Step 5: Commit**

```bash
git add ghost/mcp-server/src/core/ghost-client.ts ghost/mcp-server/test/ghost-client-read.test.ts
git commit -m "feat(ghost-mcp): ghost client read operations"
```

---

### Task 5: Ghost client — write operations

**Files:**
- Modify: `ghost/mcp-server/src/core/ghost-client.ts` (extend the `GhostClient` interface + `ghostClientFromApi` with write methods)
- Test: `ghost/mcp-server/test/ghost-client-write.test.ts`

**Interfaces:**
- Consumes: `buildLexical` (Task 3), `stripFrontmatter`/`stripLeadingH1` (Task 2), the read client (Task 4).
- Produces, added to `GhostClient`:
  - `interface PostInput = { type?: PostType; title?: string; slug?: string; markdown?: string; html?: string; tags?: Array<string>; authors?: string[]; status?: string; visibility?: string; published_at?: string; feature_image?: string; custom_excerpt?: string; meta_title?: string; meta_description?: string }`
  - `interface WriteResult = { id: string; slug: string; url: string; editorUrl: string; cardSummary?: string; cardCount?: number }`
  - `createPost(input: PostInput): Promise<WriteResult>`
  - `updatePost(input: PostInput & ({ id: string } | { slug: string })): Promise<WriteResult>`
  - `uploadImage(filePath: string): Promise<{ url: string }>`

- [ ] **Step 1: Write the failing test (writes)**

`test/ghost-client-write.test.ts`:

```ts
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/ghost-client-write.test.ts`
Expected: FAIL — `createPost`/`updatePost`/`uploadImage` are not functions.

- [ ] **Step 3: Extend `src/core/ghost-client.ts` with writes**

Add the imports at the top of the file:

```ts
import { buildLexical } from "./lexical-builder.js";
import { stripFrontmatter, stripLeadingH1 } from "./markdown.js";
```

Add these types above the `GhostClient` interface:

```ts
export interface PostInput {
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
```

Add these three method signatures to the `GhostClient` interface:

```ts
  createPost(input: PostInput): Promise<WriteResult>;
  updatePost(input: PostInput): Promise<WriteResult>;
  uploadImage(filePath: string): Promise<{ url: string }>;
```

Add a module-level helper below `editorUrl`:

```ts
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
```

Add the three methods inside the object returned by `ghostClientFromApi` (after `listTags`):

```ts
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
```

Note: `getPost`/`updatePost`/`PostInput` reference `input.id`; add `id?: string` to `PostInput` (already covers `{ id }` and `{ slug }` callers). Add one more module-level helper below `buildPayload`:

```ts
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
```

Add `id?: string;` to the `PostInput` interface.

- [ ] **Step 4: Run tests and typecheck**

Run: `cd ghost/mcp-server && npx vitest run test/ghost-client-write.test.ts && npm run typecheck`
Expected: PASS (6 tests); typecheck clean.

- [ ] **Step 5: Run the full suite**

Run: `cd ghost/mcp-server && npm test`
Expected: PASS — config, markdown, lexical-builder, ghost-client read + write (all green).

- [ ] **Step 6: Commit**

```bash
git add ghost/mcp-server/src/core/ghost-client.ts ghost/mcp-server/test/ghost-client-write.test.ts
git commit -m "feat(ghost-mcp): ghost client write operations (create/update/upload)"
```

---

### Task 6: MCP server — register read tools

**Files:**
- Create: `ghost/mcp-server/src/server.ts`
- Test: `ghost/mcp-server/test/server-read.test.ts`

**Interfaces:**
- Consumes: `GhostClient` (Tasks 4–5).
- Produces: `buildServer(client: GhostClient): McpServer` registering the four read tools (`ghost_site_info`, `ghost_post_list`, `ghost_post_get`, `ghost_tag_list`). Write tools are added in Task 7.

- [ ] **Step 1: Write the failing test**

`test/server-read.test.ts`:

```ts
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
  it("registers the four read tools", async () => {
    const mcp = await connect(fakeClient());
    const names = (await mcp.listTools()).tools.map((t) => t.name).sort();
    expect(names).toEqual(
      ["ghost_post_get", "ghost_post_list", "ghost_site_info", "ghost_tag_list"].sort(),
    );
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
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/server-read.test.ts`
Expected: FAIL — cannot find module `../src/server.js`.

- [ ] **Step 3: Implement `src/server.ts` (read tools)**

```ts
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
```

- [ ] **Step 4: Run tests and typecheck**

Run: `cd ghost/mcp-server && npx vitest run test/server-read.test.ts && npm run typecheck`
Expected: PASS (3 tests); typecheck clean.

- [ ] **Step 5: Commit**

```bash
git add ghost/mcp-server/src/server.ts ghost/mcp-server/test/server-read.test.ts
git commit -m "feat(ghost-mcp): register read tools (site_info, post_list, post_get, tag_list)"
```

---

### Task 7: MCP server — register write tools

**Files:**
- Modify: `ghost/mcp-server/src/server.ts` (add three write tools inside `buildServer`)
- Test: `ghost/mcp-server/test/server-write.test.ts`

**Interfaces:**
- Consumes: `GhostClient.createPost/updatePost/uploadImage` (Task 5), the `buildServer` test harness pattern (Task 6).
- Produces: `ghost_post_create`, `ghost_post_update`, `ghost_image_upload` registered on the same server (total tool count becomes 7).

- [ ] **Step 1: Write the failing test**

`test/server-write.test.ts`:

```ts
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/server-write.test.ts`
Expected: FAIL — only 4 tools registered; write tools missing.

- [ ] **Step 3: Add the write tools in `src/server.ts`**

Insert these three `registerTool` calls inside `buildServer`, before `return server;`:

```ts
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
    async (args) => json(await client.updatePost({ ...args, type: args.type as PostType })),
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
```

- [ ] **Step 4: Run tests and typecheck**

Run: `cd ghost/mcp-server && npx vitest run test/server-write.test.ts && npm run typecheck`
Expected: PASS (4 tests); typecheck clean.

- [ ] **Step 5: Commit**

```bash
git add ghost/mcp-server/src/server.ts ghost/mcp-server/test/server-write.test.ts
git commit -m "feat(ghost-mcp): register write tools (post_create, post_update, image_upload)"
```

---

### Task 8: Entry point + stdio transport

**Files:**
- Create: `ghost/mcp-server/src/index.ts`
- Test: `ghost/mcp-server/test/index.test.ts`

**Interfaces:**
- Consumes: `loadConfig`/`GhostConfigError` (Task 1), `createGhostClient` (Task 4), `buildServer` (Tasks 6–7).
- Produces: `main(): Promise<void>` that validates env, builds the client + server, and connects over stdio; a CLI shebang entry. On `GhostConfigError`, prints the actionable message to stderr and exits non-zero.

- [ ] **Step 1: Write the failing test**

`test/index.test.ts`:

```ts
import { describe, it, expect, vi } from "vitest";

describe("main env validation", () => {
  it("exits non-zero with an actionable message when the key is missing", async () => {
    const err = vi.spyOn(console, "error").mockImplementation(() => {});
    const exit = vi.spyOn(process, "exit").mockImplementation(((): never => {
      throw new Error("exited");
    }) as never);
    const { main } = await import("../src/index.js");
    await expect(main({})).rejects.toThrow("exited");
    expect(err).toHaveBeenCalledWith(expect.stringContaining("setup-ghost"));
    expect(exit).toHaveBeenCalledWith(1);
    err.mockRestore();
    exit.mockRestore();
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ghost/mcp-server && npx vitest run test/index.test.ts`
Expected: FAIL — cannot find module `../src/index.js`.

- [ ] **Step 3: Implement `src/index.ts`**

```ts
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
```

- [ ] **Step 4: Run tests and typecheck**

Run: `cd ghost/mcp-server && npx vitest run test/index.test.ts && npm run typecheck`
Expected: PASS (1 test); typecheck clean.

- [ ] **Step 5: Manual smoke — missing creds**

Run: `cd ghost/mcp-server && node --import tsx src/index.ts`
Expected: prints `ghost-mcp: Missing Ghost credentials...` mentioning `setup-ghost`, exits non-zero.

- [ ] **Step 6: Commit**

```bash
git add ghost/mcp-server/src/index.ts ghost/mcp-server/test/index.test.ts
git commit -m "feat(ghost-mcp): stdio entry point with env validation"
```

---

### Task 9: Build + publish wiring + README

**Files:**
- Create: `ghost/mcp-server/.npmignore`
- Create: `ghost/mcp-server/README.md`
- Modify: `ghost/mcp-server/package.json` (add `prepublishOnly`)

**Interfaces:**
- Consumes: everything above.
- Produces: a publishable package whose `dist/index.js` is the `ghost-mcp` bin; a README documenting env + tools; a verified `npm pack` artifact.

- [ ] **Step 1: Add the build-before-publish guard to `package.json`**

Add to the `scripts` block:

```json
    "prepublishOnly": "npm run build && npm test"
```

- [ ] **Step 2: Create `.npmignore`**

```
src
test
tsconfig.json
vitest.config.ts
```

- [ ] **Step 3: Create `README.md`**

```markdown
# ghost-mcp

A local stdio MCP server for the Ghost Admin API. Designed for the `ghost`
Claude Code plugin, but usable by any MCP client.

## Configuration

Set two environment variables (the `setup-ghost` skill automates this):

- `GHOST_API_URL` — your Ghost site URL, e.g. `https://yourblog.ghost.io`
- `GHOST_ADMIN_API_KEY` — the Admin API Key (`id:secret`) from a Ghost custom
  integration: Ghost Admin → Settings → Advanced → Integrations → Add custom
  integration.

## Run

    npx -y ghost-mcp@latest

## Tools

`ghost_site_info`, `ghost_post_list`, `ghost_post_get`, `ghost_post_create`,
`ghost_post_update`, `ghost_tag_list`, `ghost_image_upload`. Posts and pages
share the post tools via a `type: post | page` argument.
```

- [ ] **Step 4: Build and verify the artifact**

Run: `cd ghost/mcp-server && npm run build && npm pack --dry-run`
Expected: `dist/index.js` and other `dist/*.js` present; `npm pack --dry-run` lists only `dist/**` + `README.md` + `package.json` (no `src`/`test`).

- [ ] **Step 5: Smoke-test the built binary**

Run: `cd ghost/mcp-server && GHOST_API_URL= GHOST_ADMIN_API_KEY= node dist/index.js`
Expected: prints the `setup-ghost` credential message and exits non-zero (confirms the built entry works).

- [ ] **Step 6: Run the full suite once more**

Run: `cd ghost/mcp-server && npm test && npm run typecheck`
Expected: all tests green; typecheck clean.

- [ ] **Step 7: Commit**

```bash
git add ghost/mcp-server/.npmignore ghost/mcp-server/README.md ghost/mcp-server/package.json
git commit -m "chore(ghost-mcp): build/publish wiring + README"
```

---

## Notes for the implementer

- **Do not publish to npm in this plan.** The actual `npm publish` and the
  plugin's `.mcp.json` wiring belong to Plan 2 (skills + packaging), alongside
  the `release` skill change. This plan stops at a built, tested, pack-verified
  package.
- **`@tryghost/admin-api` is CommonJS.** With `esModuleInterop` the default
  import (`import GhostAdminAPI from "@tryghost/admin-api"`) works; if the
  runtime complains, use `import { default as GhostAdminAPI }`.
- The `WriteResult.url` prefers Ghost's returned `url`; the fallback only
  triggers if Ghost omits it.

## Self-review

- **Spec coverage:** 7 tools (Tasks 6–7) ✓; card-split lexical (Task 3) ✓;
  read-then-edit + metadata sync + slug→id (Task 5) ✓; returned URLs (Task 5) ✓;
  env auth + startup validation/actionable error (Tasks 1, 8) ✓; `type`
  post/page unification (Tasks 4–7) ✓; runtime deps limited to the three
  pure-JS packages (Task 1) ✓; `v5.0` pin (Task 4) ✓; `ghost_site_info` as the
  verifier (Task 6) ✓. Deferred-to-Plan-2 (npm publish, `.mcp.json`, skills) is
  called out explicitly.
- **Placeholder scan:** every code step contains complete code; no TBD/TODO.
- **Type consistency:** `GhostClient`, `PostInput`, `WriteResult`, `PostType`,
  `buildLexical`/`LexicalResult`, `loadConfig`/`GhostConfig` names are used
  identically across Tasks 1–8.
