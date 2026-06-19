---
name: push-draft
description: Use to push a finished local Ghost draft to the Ghost site as a draft (never published) — pull-guards against in-editor edits, uploads the feature image, creates or updates the post, verifies links, and feeds the approved post back into the style guide. Triggers on "push this to ghost", "send the draft to ghost", "publish to ghost as a draft".
---

# Push a local draft to Ghost (draft-only)

You are pushing a finished local `.md` draft to the Ghost site as a **draft**. This skill never publishes or schedules — every push sets `status: draft` without exception. Work through each phase in order.

---

## DRAFT-ONLY INVARIANT

> **`status: draft` on every single push. No exceptions.**
>
> Never set `status: published`, `status: scheduled`, or any non-draft status.
> Never call a publish or schedule endpoint. If the author asks you to publish
> directly, decline and return the editor URL — Ghost's UI is where publishing happens.

This invariant governs every phase below.

---

## Phase 1: Load config

Read `.claude/ghost.local.md` and extract:

```
Read(".claude/ghost.local.md")
```

Fields you need:

- **`drafts_dir`** — where local draft `.md` files live (default `blog-posts/drafts`).
- **`default_tags`** — tags every post gets automatically, e.g. `["engineering"]`. May be `[]`.
- **`default_visibility`** — `public`, `members`, or `paid` (default `public`).
- **`early_access.enabled`** — whether to apply the early-access paywall pattern.
- **`early_access.tag`** — tag slug to add when early-access is enabled (e.g. `"early-access"`).
- **`early_access.visibility`** — visibility override when early-access is enabled (e.g. `"paid"`).

If `ghost.local.md` does not exist, use the defaults above and note it.

### Identify the target draft

If the author provided a path, use it directly. Otherwise list the files in `drafts_dir` and ask:

> "I found these drafts in `<drafts_dir>`:
> - `<filename1>`
> - `<filename2>`
> Which one should we push?"

Read the draft file:

```
Read("<drafts_dir>/<filename>.md")
```

Parse the frontmatter to extract:

- **`title`** — post title.
- **`slug`** — if set, this is the existing Ghost post slug (update path); if absent, this is a new post (create path).
- **`tags`** — tags declared in the frontmatter (may be `[]` or absent).
- **`feature_image`** — local path or URL of the feature image (may be absent).
- **`visibility`** — per-post override; if absent, use `default_visibility`.

---

## Phase 2: Pull-guard (update path only)

**This phase applies only when the draft frontmatter contains a `slug`** (meaning the post already exists on Ghost). Skip to Phase 3 if `slug` is absent.

### 2a. Fetch the live post

```
ghost_post_get(slug="<slug>", fields="id,slug,title,lexical,updated_at,url,editorUrl")
```

Capture:
- `id` — needed for the update call in Phase 4.
- `lexical` — the live card-split content.
- `updated_at` — the live post's last-modified timestamp.

### 2b. Reconstruct live content to text

Parse the `lexical` JSON to plain text (strip card wrappers, extract `children[].text` from each card). This produces the "live version" for diffing.

### 2c. Diff live vs. local

Compare the reconstructed live text against the body of the local `.md` file (below the frontmatter).

**If the diff is empty or trivially whitespace-only** — no in-editor changes detected. Proceed to Phase 3.

**If the diff contains meaningful content changes** — someone has edited the post in the Ghost UI since the local draft was last synced. You must fold those changes in before overwriting.

Fold the in-editor changes into the LOCAL file first:

1. Show the author a summary of the diff:
   > "The live Ghost post has been edited since your local draft was last synced. Here are the differences:
   > ```diff
   > <diff output>
   > ```
   > I'll merge these changes into your local file before pushing."

2. Apply the live-post additions/changes to the local `.md` file. Where the live version and the local version conflict on the same passage, prefer the local version (the author's latest intent) but surface the conflict:
   > "Conflict in section '<heading>': the Ghost version says X; your local draft says Y. I'm keeping your local version — let me know if you want the Ghost version instead."

3. Write the merged result back to the local file:
   ```
   Edit("<drafts_dir>/<filename>.md", <old body>, <merged body>)
   ```

4. Pause and ask the author to review before continuing:
   > "Merge complete — I've folded the live Ghost edits into your local draft. Please review the updated file above, then tell me to continue when you're ready."
   
   Do not proceed to the next phase (feature image / push) until the author explicitly confirms.

**Never push to Ghost without first resolving this diff.** The pull-guard ensures you never silently clobber an in-editor edit.

---

## Phase 3: Feature image upload

If the draft frontmatter contains a `feature_image` field, check whether it is a local file path (not an https:// URL already hosted on Ghost).

**If local path:**

```
ghost_image_upload(file_path="<feature_image path>", purpose="image")
```

The tool returns a hosted URL. Record it — you will pass it as `feature_image` in Phase 4.

**If already an https:// URL** — use it as-is; no upload needed.

**If absent** — no feature image; omit the field in Phase 4.

---

## Phase 4: Resolve tags

Merge the tag list from three sources, in this order:

1. **Per-post tags** from the draft frontmatter `tags` field.
2. **`default_tags`** from `ghost.local.md` — always appended.
3. **`early_access.tag`** from `ghost.local.md` — appended only if `early_access.enabled: true`.

Deduplicate. Then resolve each tag name to its canonical slug:

```
ghost_tag_list(limit=250)
```

Match each tag in your merged list against the returned `slug` values (case-insensitive). For tags that match, use the canonical slug. For tags that are not found, note them:

> "Tag '<name>' not found in Ghost — it will be created as a new tag on push. Proceed?"

Wait for a "yes" or redirect before continuing if any new tags would be created.

---

## Phase 5: Push as a draft

**`status: draft` is mandatory. Do not deviate.**

Determine the visibility for this post:

- If `early_access.enabled: true`, use `early_access.visibility`.
- Else if the draft frontmatter has a `visibility` field, use it.
- Else use `default_visibility` from `ghost.local.md`.

### Create path (no slug in frontmatter)

```
ghost_post_create(
  title="<title>",
  markdown="<body content below frontmatter>",
  status="draft",
  tags=[{"slug": "<slug1>"}, {"slug": "<slug2>"}, ...],
  visibility="<resolved visibility>",
  feature_image="<hosted URL or omit>"
)
```

### Update path (slug present in frontmatter)

```
ghost_post_update(
  id="<id from Phase 2a>",
  title="<title>",
  markdown="<body content below frontmatter>",
  status="draft",
  tags=[{"slug": "<slug1>"}, {"slug": "<slug2>"}, ...],
  visibility="<resolved visibility>",
  feature_image="<hosted URL or omit>"
)
```

Both tools return `{id, slug, url, editorUrl, cardSummary, cardCount}`.

**After a successful push:**

1. Update the draft frontmatter `slug` field to the returned `slug` (so future pushes follow the update path):
   ```
   Edit("<drafts_dir>/<filename>.md", <old frontmatter>, <new frontmatter with slug>)
   ```

2. Return the editor URL to the author:
   > "Draft pushed. Review and publish in Ghost when you're ready:
   > <editorUrl>"

**Never set `status` to anything other than `"draft"`.** If the Ghost API returns a non-draft status in the response, log a warning and do not continue — something is wrong.

---

## Phase 6: Verify

Using the `cardSummary` and `cardCount` from the create/update response:

### 6a. Card structure check

Confirm the card count is non-zero and cardSummary shows the expected structure:

> "Card structure confirmed: <cardCount> cards. Types: <cardSummary>."

If `cardCount` is 0 or `cardSummary` is empty, warn the author:

> "Warning: the pushed post has 0 cards — the content may not have rendered correctly. Check the editor before publishing."

### 6b. Link verification

Scan the local draft body for outbound links (Markdown `[text](url)` patterns).

For each link:

1. **Internal design/journey docs** — any link whose URL matches patterns like:
   - `https://docs.google.com/...`
   - `https://www.notion.so/...`
   - `https://linear.app/...`
   - `https://github.com/<org>/<repo>/issues/...` (issue trackers)
   - Any URL that resolves to an internal planning or design artifact

   **Do not include these links without asking:**
   > "The draft links to what appears to be an internal document: `<url>`. Should I keep this link in the published draft, or remove it?"
   
   Wait for the author's explicit decision before proceeding on any internal-doc link.

2. **Public outbound links** — note each one. Do not follow or validate URLs automatically. Do not make any HTTP requests to validate links — link verification is author-side review only (you flag suspicious or internal links; the author decides). Flag any that look suspicious (e.g. localhost, IP addresses, placeholder text):
   > "Outbound links found: <count>. Please verify these are current and correct before publishing: <list>"

---

## Phase 7: Feed the style guide

On a successful push that the author is happy with — once they confirm "looks good" or equivalent:

```
/ghost:build-style-guide
```

Pass the post ID returned by the create/update call so `build-style-guide` can fold this approved post into the living style guide via its Phase 5 (continuous merge path).

> "I'll fold this approved post into the style guide now so future drafts match your voice."

If the author indicates they are not satisfied with how the post turned out (e.g. "the push worked but the content needs more work"), skip this step — do not fold in a post the author does not consider a good example of their voice.

---

## Notes

- **Draft-only invariant.** `status: draft` on every push. The Ghost UI is where the author publishes. This skill never publishes, never schedules.
- **Pull-guard always precedes an update.** Never update an existing post without first fetching and diffing the live version. The local file is the source of truth for the author's intent, but in-editor changes must not be silently discarded.
- **Tags resolved via canonical slug.** Always call `ghost_tag_list` to resolve tag names to slugs before pushing. Never pass a raw tag name to the API — Ghost matches on slug.
- **Link verification does not auto-follow URLs.** Report links for author review. The no-internal-docs rule is a hard stop: ask before linking internal planning/design artifacts.
- **Style guide feedback is conditional.** Only invoke `build-style-guide` when the author approves the pushed result as a good example of their voice.
- **If `ghost.local.md` is missing:** use defaults (`drafts_dir: blog-posts/drafts`, `default_tags: []`, `default_visibility: public`, `early_access.enabled: false`) and note it.
- **MCP tools used:** `ghost_post_get` (Phase 2, pull-guard), `ghost_image_upload` (Phase 3, feature image), `ghost_tag_list` (Phase 4, tag resolution), `ghost_post_create` (Phase 5, new post), `ghost_post_update` (Phase 5, existing post).
- **Prerequisites:** `/ghost:setup-ghost` (to configure the project and verify the Ghost connection), `/ghost:draft-post` + `/ghost:revise-post` (to produce and approve the local draft).
