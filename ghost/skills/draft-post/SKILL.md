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
generator: "ghost:draft-post"
next: "/ghost:revise-post"
---

<full prose content>
```

**The provenance note is front matter, not an HTML comment, and that is load-bearing.**
This template used to emit `<!-- DRAFT — produced by /ghost:draft-post. … -->` as the
first line of the body. Drafts are reviewed in galley (`galley edit <draft.md>`), which
REFUSES raw HTML outright — and an HTML comment is raw HTML. So every draft this skill
produced was unopenable for review, and the author had not typed a character yet: the
tool put the blocker in before the writing started. Measured 2026-08-22 against a real
corpus — 19 of 24 drafts in ghost-site refused, every one on that banner line, at lines
7-11. Front matter is parsed and skipped by galley, and `push-draft` reads named keys
and ignores the rest, so the provenance survives with nothing downstream to teach.

DO NOT put an HTML comment back into the emitted draft, here or anywhere else in this
skill. If something new needs to ride along with a draft, it goes in front matter.

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

**Tables:**
- Use **HTML inline-styled tables, not Markdown tables.** Ghost renders Markdown tables cramped, with no numeric alignment and poor mobile layout; a top-level `<table>` block is auto-split into its own clean html card. Write the HTML directly in the markdown source.
- Template — `<table style="border-collapse: collapse; width: 100%; margin: 2em 0; font-size: 0.95em;">`; header `<tr>` gets `border-bottom: 2px solid currentColor`; body `<tr>` gets `border-bottom: 1px solid rgba(128,128,128,0.25)` (drop it on the last row); cells `padding: 0.65em 1em`; numeric columns `text-align: right; font-variant-numeric: tabular-nums`.

**Headings:**
- Use sentence case (capitalize first word and proper nouns only).
- No ALL-CAPS headings.
- No headings that are purely a question mark (a question-only heading with no declarative anchor is forbidden).

Write the full draft before continuing to Phase 5. Do not truncate.

---

## Phase 5: Self-audit against anti-patterns

Once the draft is written, run the self-audit. Work through each pattern below. For each one:

1. Search the draft for the pattern (mentally or by scanning the text).
2. If any instance is found, **fix it in the file** — do not just report it.
3. After fixing, note the fix briefly.

**Anti-pattern checklist** — run all of the following in order:

**1a. ALL-CAPS headings**
Grep: `grep -nE '^#{1,6} [A-Z][A-Z ]{3,}$'`
Fix: Convert to sentence case — capitalize only the first word and any proper nouns.

**1b. Question-only headings**
Grep: `grep -nE '^#{1,6} .+\?$'`
Fix: Rewrite as a declarative or partially declarative heading. Example: "Why this approach breaks at scale" instead of "Why does this break at scale?"

**2. Editorial restatements**
Grep: `grep -niE '(in other words|to put it simply|what i mean is|what i(''m| am) saying is|let me rephrase|put another way)'`
Fix: Delete the restatement and revise the sentence it was clarifying so it stands on its own.

**3. Hedge words**
Grep: `grep -niE '\b(just|simply|basically|obviously|of course|clearly|needless to say)\b'`
Fix: Delete the hedge word. If the sentence still sounds uncertain, rewrite the claim more precisely.

**4. AI-flavored transitions and filler phrases**
Grep: `grep -niE '(in conclusion|in summary|to summarize|it(''s| is) worth noting|it(''s| is) important to (note|remember|understand)|delve into|certainly|absolutely|moreover,|furthermore,|additionally,)'`
Fix: Delete the phrase and restructure the sentence or paragraph to flow without it.

**5. Cleft and focus-frame constructions**
Grep: `grep -niE '(what (this|that) means is|the thing about .{1,40} is|what(''s| is) (interesting|important|notable) (here|about this) is|the (point|key|takeaway) (here|is that))'`
Fix: Delete the frame and state the point directly. "What this means is the cache is invalidated" → "The cache is invalidated."

**6. Cute closers**
Grep: `grep -niE '(happy coding|until next time|stay curious|hope this helps|happy (building|shipping|hacking)|that(''s| is) a wrap|catch you (next time|later)|keep (coding|building|hacking))'`
Fix: Delete the phrase. Replace with a closing line that reinforces the post's main point, poses an open question, or points to a logical next step.

**7a. Missing language tag on code fence**
Flag any fenced code block whose opening fence has no language tag (a bare triple-backtick with nothing after it).
Fix: Add the correct language tag. Defaults: `typescript`, `javascript`, `bash`, `json`, `yaml`, `text`.

**7b. Code fence lines exceeding 70 characters**
Flag any line inside a fenced code block longer than ~70 characters (Ghost renders code narrow).
Fix: Break long lines using the language's idiomatic line-continuation style. For shell: `\` continuation. For TypeScript/JavaScript: intermediate variables or line breaks at operators.

**8. Markdown tables**
Grep: `grep -nE '^\|.*\|.*\|' ` — flags GitHub-style Markdown table rows (and the `|---|---|` separator).
Fix: Convert to an HTML inline-styled table (see Tables guidance in Phase 4b). Markdown tables render cramped in Ghost and are not split into their own card.

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

## Phase 5b: Reading pass — the tells a grep can't catch

The greps in Phase 5 catch fixed strings. The tells that make writing read as AI are mostly **not** fixed strings — they are rhythm and framing, and they only surface on a read. A clean grep is not a clean draft. Read the whole draft once more, section by section, and fix each of the following before you show anything. When unsure, read the sentence out loud: **if you wouldn't actually say it, it's a tell.**

- **Choppy rhythm.** Plain does not mean short. A run of short declaratives reads as mechanical; substantive sentences that connect cause and effect are the voice. Rewrite staccato runs into connected sentences and vary length.
  - _Choppy:_ "Publishing runs in CI. There's no separate step. Shipping is tagging a release."
  - _Connected:_ "Publishing happens in CI on a pushed tag, so releasing is nothing more than tagging a clean version."
- **Cleft / focus-frame.** "X is what Y", "the X is that", "what X is is Y" — lead with the subject.
  - _Before:_ "The server is what the skills reach Ghost through." → _After:_ "The skills reach Ghost through the server."
- **Manufactured contrast.** "X is easy; Y is the hard part" is a tidy setup that reads as AI. Describe what actually happened instead.
- **Em-dash reveal.** "[claim] — and that turned out to be [payoff]." Drop the reveal; end on the fact.
- **Retcon.** Do not dress a fix up as intentional design. Describe what the thing does and why, not a story of having meant it all along.
  - _Before:_ "That's deliberate: the server stays up so…" → _After:_ "The server stays up rather than exiting, because exiting surfaces only an opaque error."
- **Overselling.** "I set one rule at the start", "the part I lean on". Understate — it's a goal or a handy feature, not a manifesto.
- **Negative-first.** Lead with the reason, not the absence.
  - _Before:_ "Pages don't get their own tools." → _After:_ "Because a page is the same object as a post, the tools take a `type` argument."
- **Slip-narration.** Present the working config, not a blow-by-blow of what broke and how it got fixed.

Fix these in the file. Only then continue to the hand-off.

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
