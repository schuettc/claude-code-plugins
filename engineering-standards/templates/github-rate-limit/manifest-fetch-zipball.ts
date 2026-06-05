import * as YAML from "js-yaml";
import { unzipSync, strFromU8 } from "fflate";
import { withRateLimitRetry } from "./rate-limit-backoff.js";
import {
  WorkshopManifestSchema,
  LessonManifestSchema,
  type WorkshopManifest,
  type LessonManifest,
} from "./schema.js";

/**
 * Abstraction over file access in a remote repo. CI uses a real
 * GitHub-App-backed implementation; tests pass an in-memory map.
 */
export interface FileFetcher {
  /** Returns file contents at path, or null if missing. */
  readFile(path: string): Promise<string | null>;
  /** Returns immediate child directory names under path. */
  listDir(path: string): Promise<string[]>;
}

export interface FetchedWorkshop {
  workshop: WorkshopManifest;
  lessonsByKey: Map<string, LessonManifest>;
  landing: string;
  /**
   * Body of the workshop's `.claude/skills/workshop-orchestrator/SKILL.md`
   * (or legacy `.claude/skills/workshop-orchestrator.md`). Null when neither
   * file is present — that means the workshop is builder-mode only and
   * won't surface in the Cowork catalog.
   */
  orchestratorProse: string | null;
  /**
   * Per-lesson `SKILL.md` bodies, keyed by lesson id (matches
   * `lessonsByKey`'s keys). Missing entries mean that lesson directory
   * had no `SKILL.md` — recorded as null so the bundler can serialize
   * "intentionally absent" cleanly.
   */
  lessonProseByKey: Map<string, string | null>;
}

export interface FetchOptions {
  repo: string; // "owner/name" — informational; fetcher carries auth
  ref: string;
  fetcher: FileFetcher;
  /**
   * Optional: sub-directory within the repo where this workshop's manifest
   * lives. When set, all file paths are prefixed with `<workshopRoot>/`.
   * Trailing slashes are stripped before use. Omit for single-workshop repos
   * where workshop.yaml is at the repo root (the default).
   * Example: ".workshop/claude-code"
   */
  workshopRoot?: string;
}

export async function fetchWorkshopFromRepo(
  opts: FetchOptions,
): Promise<FetchedWorkshop> {
  // Normalise workshopRoot: strip trailing slash, produce empty string when absent.
  const root = opts.workshopRoot ? opts.workshopRoot.replace(/\/$/, "") : "";
  const p = (rel: string) => {
    if (!root) return rel;
    if (!rel) return root;
    return `${root}/${rel}`;
  };

  const wsRaw = await opts.fetcher.readFile(p("workshop.yaml"));
  if (wsRaw === null) {
    throw new Error(`${opts.repo}@${opts.ref}: workshop.yaml not found`);
  }
  const workshop = WorkshopManifestSchema.parse(YAML.load(wsRaw));

  const landing = (await opts.fetcher.readFile(p("landing.md"))) ?? "";

  // Lesson dirs may sit either under a `workshop/` subdir (single-repo
  // workshops follow this convention) OR directly under the workshop root
  // (monorepo workshops, where the workshopRoot itself is the workshop's
  // home and a redundant `workshop/` nest would be ceremony). Try the
  // subdir first; fall back to the flat layout.
  const subdirListing = await opts.fetcher.listDir(p("workshop"));
  const useFlat = subdirListing.length === 0;
  const lessonParent = useFlat ? "" : "workshop/";
  const dirs = useFlat ? await opts.fetcher.listDir(p("")) : subdirListing;

  const lessonsByKey = new Map<string, LessonManifest>();
  const lessonProseByKey = new Map<string, string | null>();
  for (const dir of dirs) {
    if (!/^lesson_/.test(dir)) continue; // ignore non-lesson siblings (src/, tests/, etc.)
    const yamlText = await opts.fetcher.readFile(p(`${lessonParent}${dir}/lesson.yaml`));
    if (yamlText === null) continue;
    const lesson = LessonManifestSchema.parse(YAML.load(yamlText));
    const key = dirFromPath(dir);
    lessonsByKey.set(key, lesson);
    // Per-lesson SKILL.md body. Absence is non-fatal (builder-mode workshops
    // may not ship director-mode prose at all).
    const skill = await opts.fetcher.readFile(
      p(`${lessonParent}${dir}/SKILL.md`),
    );
    lessonProseByKey.set(key, skill);
  }

  // Orchestrator skill prose. Modern path first, legacy single-file fallback.
  // Absence is non-fatal — workshop will simply not surface in Cowork.
  let orchestratorProse = await opts.fetcher.readFile(
    p(".claude/skills/workshop-orchestrator/SKILL.md"),
  );
  if (orchestratorProse === null) {
    orchestratorProse = await opts.fetcher.readFile(
      p(".claude/skills/workshop-orchestrator.md"),
    );
  }

  return { workshop, lessonsByKey, landing, orchestratorProse, lessonProseByKey };
}

/**
 * Lesson dirs are named `lesson_<slug>` (slug form, no numeric prefix);
 * phases reference bare slugs (e.g. "install"). Strip the `lesson_` prefix
 * to get the phase key.
 */
function dirFromPath(dir: string): string {
  // "lesson_install" -> "install"
  return dir.replace(/^lesson_/, "");
}

export { dirFromPath as _dirFromPathForTest };

export interface GitHubFileFetcherOptions {
  repo: string; // "owner/name"
  ref: string; // branch, tag, or sha
  token: string; // installation token from mintInstallationToken()
  /** Test seam — injectable fetch. Defaults to global fetch. */
  fetch?: typeof fetch;
  /** Test seam — injectable sleep. Defaults to setTimeout-based sleep. */
  sleep?: (ms: number) => Promise<void>;
  /** Max retries on rate-limit responses. Defaults to 3. */
  maxRetries?: number;
}

/**
 * Download the repo's entire zipball at `ref` ONCE, unpack with fflate, and
 * serve all subsequent readFile / listDir calls from in-memory maps. This
 * replaces a per-file /contents/{path} pattern that was making ~25 API calls
 * per workshop. Drops a Deploy from ~400 calls to ~16 (workshops × 2 passes).
 */
export async function createGitHubFileFetcher(
  opts: GitHubFileFetcherOptions,
): Promise<FileFetcher> {
  const fetchFn = opts.fetch ?? fetch;
  const sleep = opts.sleep ?? ((ms: number) => new Promise<void>((r) => setTimeout(r, ms)));
  const url = `https://api.github.com/repos/${opts.repo}/zipball/${encodeURIComponent(opts.ref)}`;
  const headers = {
    Authorization: `Bearer ${opts.token}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };

  const res = await withRateLimitRetry(
    () => fetchFn(url, { headers }),
    { maxRetries: opts.maxRetries ?? 3, sleep },
  );
  if (!res.ok) {
    throw new Error(
      `GitHub zipball ${opts.repo}@${opts.ref}: ${res.status} ${await res.text()}`,
    );
  }
  const raw = new Uint8Array(await res.arrayBuffer());
  const unzipped = unzipSync(raw);

  // Detect and strip the top-level dir (e.g. "owner-repo-shortsha/").
  const keys = Object.keys(unzipped);
  if (keys.length === 0) {
    throw new Error(`GitHub zipball ${opts.repo}@${opts.ref}: empty archive`);
  }
  const prefix = keys[0]!.split("/", 1)[0]!;
  const prefixWithSlash = `${prefix}/`;

  const filesByPath = new Map<string, Uint8Array>();
  const dirChildren = new Map<string, Set<string>>(); // dir → child names (files + dirs)

  for (const [key, content] of Object.entries(unzipped)) {
    if (!key.startsWith(prefixWithSlash)) continue;
    const rel = key.slice(prefixWithSlash.length);
    if (rel.length === 0) continue;
    const isDirEntry = rel.endsWith("/");
    const cleaned = isDirEntry ? rel.slice(0, -1) : rel;
    if (!cleaned) continue;
    if (!isDirEntry) filesByPath.set(cleaned, content);

    // Index every ancestor dir → immediate child.
    const parts = cleaned.split("/");
    for (let i = 0; i < parts.length; i += 1) {
      const parent = parts.slice(0, i).join("/");
      const child = parts[i]!;
      if (!dirChildren.has(parent)) dirChildren.set(parent, new Set());
      dirChildren.get(parent)!.add(child);
    }
  }

  function isDir(path: string): boolean {
    return dirChildren.has(path);
  }

  return {
    async readFile(path) {
      const content = filesByPath.get(path);
      if (!content) return null;
      return strFromU8(content);
    },
    async listDir(path) {
      const children = dirChildren.get(path);
      if (!children) return [];
      // Match existing impl: return immediate-subdirectory names only.
      return [...children].filter((name) => {
        const sub = path ? `${path}/${name}` : name;
        return isDir(sub);
      });
    },
  };
}
