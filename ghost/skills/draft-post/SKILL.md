---
name: draft-post
description: Use to write the first full draft of a Ghost blog post locally, matching the author's style guide, then self-audit it against the anti-pattern checklist. Triggers on "draft a post about X", "write the first draft", "start a new blog post".
---

# Draft a Ghost blog post

You are writing the first full draft of a blog post and saving it locally. No Ghost round-trips — this skill writes only to the local filesystem. Work through each phase in order.

---

## Phase 1: Load config

Read `.claude/ghost.local.md` and extract:

```
Read(".claude/ghost.local.md")
```

Fields you need:

- **`drafts_dir`** — where local draft `.md` files live (default `blog-posts/drafts`).
- **`style_guide_path`** — path to the style guide (default `.claude/ghost-style-guide.md`).

If `ghost.local.md` does not exist, use the defaults above.

---

## Phase 2: Load the style guide

Read the style guide at `style_guide_path`:

```
Read("<style_guide_path>")
```

Parse and internalize all four sections:

- **Stated voice** — audience, reader outcome, tone, admired references, explicit avoidances, structural preferences. This is authoritative; follow it literally.
- **Observed patterns** — typical length, sentence rhythm, paragraph rhythm, opening/closing moves, structural moves, vocabulary register, formatting habits, PoV/tense.
- **Anti-patterns** — the full list of forbidden patterns. You will run these as a self-audit in Phase 5.
- **Provenance log** — note which posts have been folded in (for context only).

If the style guide does not exist: note "no style guide found — run `/ghost:build-style-guide` first". Continue with generic best-practice prose but warn the author the draft is not style-matched.

---

## Phase 3: Plan — settle angle and outline

Before writing a single word of prose, settle the angle and structure.

### 3a. Check for topic overlap (optional)

If the Ghost MCP connection is available, call:

```
ghost_post_list(filter="status:published", limit=50, fields="id,title,url")
```

Scan the returned titles. If an existing post covers essentially the same topic and angle, surface that to the author:

> "I found an existing post that may overlap: '<title>' (<url>). Would you like to take a distinct angle, or is this a follow-up?"

Wait for the author's direction before continuing. If `ghost_post_list` is unavailable or fails, skip this check silently and continue.

### 3b. Confirm the angle

State the specific angle in one sentence — what claim or insight this post makes, and for whom. If the author gave you a topic but not an angle, propose one and ask for a quick confirm before outlining:

> "Proposed angle: <one sentence>. Does that fit what you had in mind?"

Wait for confirmation (a quick "yes" or redirect is enough) before continuing.

### 3c. Build the outline

Produce a lightweight outline:

- **Title (working):** a concrete, non-clickbait title.
- **Opening move:** which pattern from the Observed patterns (anecdote / assertion / code example / problem statement / question). Match the author's typical opening style.
- **Body sections:** 3–5 section headings with a one-line summary of what each covers.
- **Closing move:** which pattern from the Observed patterns (summary / open question / CTA / sign-off). Match the author's typical close.
- **Estimated word count:** based on the Observed patterns range.
- **Code examples:** list any that belong in the post (title + language).

Show the outline to the author and confirm before drafting. A quick "looks good" is sufficient. A redirect at this stage costs seconds; a redirect after a full draft costs minutes.

---

## Phase 4: Draft to the local file

Once the outline is confirmed, write the full draft.

### 4a. Derive the filename

Slug the working title: lowercase, hyphens for spaces, remove punctuation.

```
<drafts_dir>/<YYYY-MM-DD>-<slugified-title>.md
```

Example: `blog-posts/drafts/2026-06-19-shipping-faster-with-preflight-checks.md`

### 4b. Write the draft

Write the complete draft to the filename derived above. The draft file must use this structure:

```
Write("<drafts_dir>/<filename>.md", <full draft content>)
```

```markdown
---
title: "<working title>"
status: draft
date: <YYYY-MM-DD>
tags: []
---

<!-- DRAFT — produced by /ghost:draft-post. Run /ghost:revise-post to refine. -->

<full prose content>
```

Apply every constraint from the style guide as you write:

**From Stated voice:**
- Write for the stated audience at the stated knowledge level.
- Pursue the stated reader outcome — the draft should deliver on it by the close.
- Maintain the stated tone throughout (use the author's own adjectives as a check: does this paragraph sound like those three words?).
- Avoid every item in the "Avoid" list.
- Follow every structural preference (hook type, paragraph length, use of bullets/code, opening/closing pattern).

**From Observed patterns:**
- Target the observed word count range (stay within ±20%).
- Match sentence rhythm: if the author writes short punchy sentences, do not write sprawling multi-clause structures, and vice versa.
- Match paragraph rhythm: if the author uses frequent one-sentence paragraphs, use them; if not, don't.
- Match PoV and tense.
- Format code blocks the way the author does (frequency, placement, context).

**Code fences:**
- Always include a language tag: ` ```typescript `, ` ```bash `, etc. Never a bare ` ``` `.
- Keep lines to ≤70 characters inside code blocks (Ghost's rendering wraps at narrow widths).

**Headings:**
- Use sentence case (capitalize first word and proper nouns only).
- No ALL-CAPS headings.
- No headings that are purely a question mark (a question-only heading with no declarative anchor is forbidden).

Write the full draft before continuing to Phase 5. Do not truncate.

---

## Phase 5: Self-audit against anti-patterns

Once the draft is written, run the self-audit. Open the anti-pattern checklist:

```
Read("${CLAUDE_PLUGIN_ROOT}/skills/draft-post/anti-patterns.md")
```

Work through each pattern in the checklist. For each one:

1. Search the draft for the pattern (mentally or by scanning the text).
2. If any instance is found, **fix it in the file** — do not just report it.
3. After fixing, note the fix briefly.

**Fix, don't just report.** The self-audit is a repair pass, not a linting report. When the audit is complete, the draft file should already be clean.

After the full audit pass, write the corrected draft back to the same file (overwrite). Then report:

```
Self-audit complete.
  Patterns checked: <n>
  Issues found and fixed: <n>
  Fixes applied:
    - [pattern name]: <what was fixed>
    - ...
  No issues found for: <list of clean patterns>
```

If no issues were found, say so — "All patterns clean."

---

## Phase 6: Confirm and hand off

After the audit, confirm the draft is ready for review:

> "Draft written to `<path>` and self-audited. <n> issues found and fixed.
>
> Run `/ghost:revise-post` to refine it — pass the draft path if needed."

Do not push to Ghost. Do not call any Ghost MCP write tools. The draft lives locally until `/ghost:revise-post` approves it for `/ghost:push-draft`.

---

## Notes

- **Local only.** The only write operation is to `<drafts_dir>/<filename>.md`. The only optional MCP call is `ghost_post_list` (read-only) in Phase 3a to check for topic overlap. No Ghost write tools are called.
- **Style guide is the source of truth.** If the style guide and any other guidance conflict, the style guide wins.
- **If `ghost.local.md` is missing:** use defaults (`drafts_dir: blog-posts/drafts`, `style_guide_path: .claude/ghost-style-guide.md`) and note it.
- **If the style guide is missing:** draft using generic best-practice prose. Warn the author and recommend running `/ghost:build-style-guide` before the next draft.
- **Prerequisites:** `/ghost:setup-ghost` (to configure the project), `/ghost:define-voice` + `/ghost:build-style-guide` (to produce the style guide the draft matches against).
- MCP tools optionally used: `ghost_post_list` (Phase 3a, read-only, skipped on failure).
