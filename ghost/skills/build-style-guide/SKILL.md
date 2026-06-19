---
name: build-style-guide
description: Use to create or update the per-author Ghost style guide from all available signals — interview answers, reference docs, and the published corpus — and to fold a newly approved post into it. Triggers on "build my style guide", "update the style guide", "learn my voice from my posts", and is invoked by push-draft after a successful push.
---

# Build the Ghost style guide

You are synthesizing a living, per-author style guide from all available signals: interview answers, reference material, and the published corpus. The guide lives at the path set in `style_guide_path` (default `.claude/ghost-style-guide.md`).

Work through each phase in order. Do not skip a phase — each feeds the next.

---

## Phase 1: Load config and inputs

### 1a. Read project config

Read `.claude/ghost.local.md` and extract the frontmatter fields:

```
Read(".claude/ghost.local.md")
```

The fields you need:

- **`corpus_filter`** — NQL filter for corpus pull (default `status:published`).
- **`corpus_limit`** — max posts to pull (default `25`).
- **`style_guide_path`** — output path for the style guide (default `.claude/ghost-style-guide.md`).

If `ghost.local.md` does not exist, use the defaults above. Note it in your working notes.

### 1b. Read the voice-inputs handoff

Read the interview answers and reference notes written by `/ghost:define-voice`:

```
Read(".claude/ghost-voice-inputs.md")
```

This file is the **authoritative source for Stated voice**. Parse it into:

- Interview answers (Q1–Q6)
- Reference notes (one block per source, with tone/structure/quotes)

If the file does not exist, continue — this is the cold-start-without-interview path. The Stated voice section will be sparse; note that explicitly in the guide.

### 1c. Check whether a style guide already exists

```
Read("<style_guide_path>")
```

If it exists: you are in **merge mode** — preserve the existing Stated voice section verbatim. Continue to Phase 2.

If it does not exist: you are in **initial build mode** — you will create it from the template. Continue to Phase 2.

---

## Phase 2: Pull the corpus

### 2a. Verify the Ghost connection

```
ghost_site_info()
```

If this fails (auth error, connection refused): skip corpus pull, note "corpus unavailable — Ghost not connected", and proceed with interview-only inputs. The guide will still be valid; the Observed patterns section will be empty.

### 2b. List published posts

```
ghost_post_list(filter="<corpus_filter>", limit=<corpus_limit>, fields="id,title,published_at,url")
```

Capture the list. If no posts are returned, note "no published posts found" and proceed.

### 2c. Fetch post content

For each post in the list (up to `corpus_limit`), fetch the full content:

```
ghost_post_get(id="<post_id>", fields="title,html,plaintext,published_at,url")
```

Prefer `plaintext` for analysis; fall back to `html` if `plaintext` is absent.

Work through all posts before moving to Phase 3. This is the most time-consuming step — process them in order, extracting style signals as you go.

**Cold start without corpus:** If `ghost_site_info` failed or returned no posts, skip Phase 2b–2c and proceed directly to Phase 3.

---

## Phase 3: Synthesize the four sections

Build or update each section. Keep the rules for each section strictly separate — they serve different purposes and different update policies.

### Section 1 — Stated voice (authoritative; never auto-overwritten)

**In initial build mode:** Derive this section from the interview answers in `.claude/ghost-voice-inputs.md`. Map each field directly:

- **Audience** → Q1 answer (verbatim, lightly paraphrased if the author was verbose)
- **Reader outcome** → Q2 answer
- **Tone** → Q3 answer — preserve the author's exact adjectives or phrase
- **Admired references** → Q4 answer (names + what the author said they admire)
- **Avoid** → Q5 answer — record every specific item the author mentioned
- **Structural preferences** → Q6 answer

If no interview exists, write placeholder values and note that `/ghost:define-voice` should be run first.

**In merge mode:** Read the existing Stated voice section from the style guide and carry it forward unchanged. Do not re-derive it from the interview. The author's edits are intentional and must be preserved. If there is new interview material (a re-run of `define-voice`), surface the delta for explicit confirmation before updating.

### Section 2 — Observed patterns (refreshable; re-derived each run)

Analyze all fetched posts together. Derive:

- **Typical post length** — word count range (min, median, max across the corpus)
- **Sentence rhythm** — average sentence length, variation, use of short punchy sentences vs. long flowing ones
- **Paragraph rhythm** — typical paragraph length in sentences; how often one-sentence paragraphs appear
- **Opening moves** — how posts typically begin (anecdote, question, assertion, code example, context-setting)
- **Closing moves** — how posts typically end (summary, CTA, open question, sign-off)
- **Structural moves** — recurring transitions, section patterns, use of subheadings
- **Vocabulary register** — technical density (jargon, acronyms), formality level
- **Formatting habits** — frequency and style of code blocks, bullet lists, numbered lists, callouts, images
- **PoV and tense** — first/second/third person, past/present

Write these as concise observations, not prescriptions. Each observation should cite at least one example post by title.

If no corpus was available, write: _"No corpus folded in. Run `/ghost:build-style-guide` after publishing posts to populate this section."_

### Section 3 — Anti-patterns (refreshable; re-derived each run)

Combine two sources:

1. **From the interview** — Q5 (what to avoid). Translate each stated avoidance into a concrete pattern description. Example: "no jargon" → "Avoid insider acronyms without expansion on first use."
2. **From corpus analysis** — flag any patterns from the Observed section that conflict with the Stated voice. Also flag any of these house anti-patterns if you observe them:
   - Forbidden heading styles: ALL-CAPS headings, question-mark-only headings
   - Editorial restatements: "In other words…", "To put it simply…", "What I mean is…"
   - Hedge words: "just", "simply", "basically", "obviously", "of course"
   - AI-flavored transitions: "In conclusion", "It's worth noting that", "It's important to remember", "Delve into", "Certainly"
   - Cleft / focus-frames: "What this means is…", "The thing about X is…", "What's interesting here is…"
   - Cute closers: "Happy coding!", "Until next time!", "Stay curious!", "Hope this helps!"
   - Code-fence width: code blocks without a language tag, or lines exceeding ~70 columns (Ghost renders narrow)

List each anti-pattern as a short bullet with a concrete example of what to avoid.

If no corpus and no interview: write the house defaults list above as baseline anti-patterns.

### Section 4 — Provenance log (idempotent append-only)

**In initial build mode:** Create the table with one row per source:

| Date | Source | Type | Notes |
|------|--------|------|-------|
| `<today>` | `.claude/ghost-voice-inputs.md` | interview | Initial build |
| `<today>` | `<post title>` | corpus-post | Folded in on initial build |

Add one row per post fetched. If no corpus was available, note that.

**In merge mode:** Read the existing provenance log. Append new rows for any posts not already listed. Never delete existing rows. The log is the audit trail of what shaped the guide.

---

## Phase 4: Write the style guide

Write the complete four-section document to `<style_guide_path>`.

Use the following skeleton as the file structure. Update the frontmatter fields:

- `last_updated`: today's date (ISO 8601)
- `sources_count`: total number of posts folded in across all runs (from the provenance log)

Write the file with this exact structure:

```markdown
---
# Ghost style guide — generated by /ghost:build-style-guide
# DO NOT hand-edit the Observed patterns or Provenance log sections — they are re-derived on each merge.
# Edit only the Stated voice section to add or refine authoritative voice guidance.
generated_by: ghost:build-style-guide
last_updated: "<YYYY-MM-DD>"
sources_count: <n>
---

# Ghost Style Guide

_Generated by `/ghost:build-style-guide`. The Stated voice section is authoritative and human-controlled; all other sections are derived and refreshable._

---

## Stated voice

<!-- SOURCE: Interview answers from .claude/ghost-voice-inputs.md — NEVER auto-overwritten. -->
<!-- Edit this section directly to add or revise authoritative voice rules. -->

**Audience:** <derived from interview Q1 or placeholder>

**Reader outcome:** <derived from interview Q2 or placeholder>

**Tone:** <derived from interview Q3 or placeholder>

**Admired references:** <derived from interview Q4 or placeholder>

**Avoid:** <derived from interview Q5 or placeholder>

**Structural preferences:** <derived from interview Q6 or placeholder>

---

## Observed patterns

<!-- SOURCE: Derived from the published corpus via ghost_post_list / ghost_post_get. -->
<!-- Re-derived on each /ghost:build-style-guide merge run — safe to overwrite this block. -->

<derived observations, or placeholder if no corpus>

---

## Anti-patterns

<!-- SOURCE: Synthesized from interview (avoid list) + cross-checked against corpus + house defaults. -->
<!-- Re-derived on each merge run — safe to overwrite this block. -->

<derived anti-patterns, or house defaults if no corpus/interview>

---

## Provenance log

<!-- SOURCE: Idempotent append-only log of every post and reference folded into this guide. -->
<!-- Append new entries; never delete existing ones. -->

| Date | Source | Type | Notes |
|------|--------|------|-------|
<one row per source>
```

After writing, confirm the file was saved and report:

- Path where the guide was written
- How many posts were folded in
- Whether this was an initial build or a merge
- Whether the Stated voice section is interview-derived, carried forward from a prior run, or placeholder-only

---

## Phase 5: Continuous merge (post-push path)

This phase applies when `build-style-guide` is invoked by `/ghost:push-draft` after a successful push of a newly approved post, or when the author manually runs it after publishing a new post.

### 5a. Identify the new post

The caller (push-draft or the author) provides the post ID or title. Fetch it:

```
ghost_post_get(id="<new_post_id>", fields="title,html,plaintext,published_at,url")
```

### 5b. Check provenance log

Read the existing style guide's provenance log. If this post is already listed, this is a no-op — confirm "already folded in" and stop.

### 5c. Re-derive Observed patterns

Fetch the current corpus (same filter/limit as Phase 2) plus the new post. Re-derive the Observed patterns section with the expanded dataset.

### 5d. Surface guidance changes for confirm

Before writing, diff the new Observed patterns against the existing ones. If any observation changed meaningfully (e.g., average post length shifted, a new structural pattern emerged), surface those changes explicitly:

> "The Observed patterns section would change in these ways:
> - Average post length: 850 words → 920 words
> - Opening moves: adds 'problem statement' pattern (3 of 10 posts now use it)
>
> The Stated voice section will not be changed. Approve these updates? [y/n]"

Wait for explicit confirmation before writing. If the author says no, do not update the file.

### 5e. Never override Stated voice

Do not touch the Stated voice section under any circumstances during continuous merge. The author's intentional edits are permanent until they explicitly re-run `/ghost:define-voice` and then confirm an update.

### 5f. Append to provenance log

Add one row for the new post. Write the updated file.

---

## Notes

- **Cold start (no corpus, no interview):** The guide is created with house-default anti-patterns and placeholder Stated voice. It is valid and usable; it just needs more signal. Run `/ghost:define-voice` first, then re-run this skill.
- **Cold start (interview only, no corpus):** Stated voice is fully populated from the interview. Observed patterns and anti-patterns are partially populated (interview-derived avoidances + house defaults). Add corpus once posts are published.
- **Cold start (corpus only, no interview):** Observed patterns and anti-patterns are fully derived. Stated voice will be placeholder. Run `/ghost:define-voice` to fill it in, then re-run this skill.
- **The Stated voice section is the author's voice.** It must never be overwritten silently. Only the author can change it — either by editing the file directly or by re-running `/ghost:define-voice` and explicitly confirming an update.
- **The style guide is the source of truth** for all writing skills in the ghost plugin. If the guide and the handoff file disagree, the guide wins (it may contain post-interview edits).
- MCP tools used: `ghost_site_info`, `ghost_post_list`, `ghost_post_get`. Config keys read: `corpus_filter`, `corpus_limit`, `style_guide_path` from `.claude/ghost.local.md`.
