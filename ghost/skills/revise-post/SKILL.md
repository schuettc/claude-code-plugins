---
name: revise-post
description: Use to revise an existing local Ghost draft section by section with the author, improving formatting, voice, and accuracy. Triggers on "revise this post", "let's go through it section by section", "tighten this draft".
---

# Revise a Ghost blog post draft

You are revising an existing local draft in `drafts_dir` — no Ghost round-trips. Every change stays on the local filesystem until the author hands off to `/ghost:push-draft`. Work through each section interactively, one at a time, applying all three axes before moving on.

---

## Phase 1: Load config and locate the draft

Read `.claude/ghost.local.md` and extract:

```
Read(".claude/ghost.local.md")
```

Fields you need:

- **`drafts_dir`** — where local draft `.md` files live (default `blog-posts/drafts`).
- **`style_guide_path`** — path to the style guide (default `.claude/ghost-style-guide.md`).

If `ghost.local.md` does not exist, use the defaults above.

### Identify the target draft

If the author provided a path, use it directly. Otherwise, list the files in `drafts_dir` and ask the author to confirm which draft to revise:

> "I found these drafts in `<drafts_dir>`:
> - `<filename1>`
> - `<filename2>`
> Which one should we revise?"

Read the draft file:

```
Read("<drafts_dir>/<filename>.md")
```

If the draft file does not exist, stop and tell the author:

> "No draft found at `<path>`. Run `/ghost:draft-post` to create one first."

---

## Phase 2: Load the style guide

Read the style guide at `style_guide_path`:

```
Read("<style_guide_path>")
```

Parse and internalize all four sections (Stated voice, Observed patterns, Anti-patterns, Provenance log). The style guide governs voice and formatting decisions throughout revision.

If the style guide does not exist, continue the revision but warn the author:

> "No style guide found at `<path>`. Voice corrections will fall back to generic best-practice prose. Run `/ghost:build-style-guide` to generate a style-matched guide."

---

## Phase 3: Anti-pattern checklist (inlined)

The following anti-patterns govern the voice axis in Phase 5. Keep them active throughout revision.

**1a. ALL-CAPS headings**
Grep: `grep -nE '^#{1,6} [A-Z][A-Z ]{3,}$'`
Fix: Convert to sentence case — capitalize only the first word and any proper nouns.

**1b. Question-only headings**
Grep: `grep -nE '^#{1,6} .+\?$'`
Fix: Rewrite as a declarative or partially declarative heading.

**2. Editorial restatements**
Grep: `grep -niE '(in other words|to put it simply|what i mean is|what i(''m| am) saying is|let me rephrase|put another way)'`
Fix: Delete the restatement and revise the sentence it was clarifying.

**3. Hedge words**
Grep: `grep -niE '\b(just|simply|basically|obviously|of course|clearly|needless to say)\b'`
Fix: Delete the hedge word; rewrite the claim more precisely if needed.

**4. AI-flavored transitions and filler phrases**
Grep: `grep -niE '(in conclusion|in summary|to summarize|it(''s| is) worth noting|it(''s| is) important to (note|remember|understand)|delve into|certainly|absolutely|moreover,|furthermore,|additionally,)'`
Fix: Delete the phrase; restructure the sentence or paragraph to flow without it.

**5. Cleft and focus-frame constructions**
Grep: `grep -niE '(what (this|that) means is|the thing about .{1,40} is|what(''s| is) (interesting|important|notable) (here|about this) is|the (point|key|takeaway) (here|is that))'`
Fix: Delete the frame; state the point directly.

**6. Cute closers**
Grep: `grep -niE '(happy coding|until next time|stay curious|hope this helps|happy (building|shipping|hacking)|that(''s| is) a wrap|catch you (next time|later)|keep (coding|building|hacking))'`
Fix: Delete the phrase; replace with a closing line that reinforces the post's main point.

**7a. Missing language tag on code fence**
Flag any fenced code block whose opening fence has no language tag (a bare triple-backtick with nothing after it).
Fix: Add the correct language tag (`typescript`, `javascript`, `bash`, `json`, `yaml`, `text`).

**7b. Code fence lines exceeding 70 characters**
Flag any line inside a fenced code block longer than ~70 characters (Ghost renders code narrow).
Fix: Break long lines using the language's idiomatic line-continuation style.

---

## Phase 4: Parse the draft into sections

Split the draft on its Markdown headings (`##`, `###`). Treat the frontmatter block and any content before the first heading as section 0 ("preamble"). Each subsequent heading + its body text is one section.

Build a section list:

```
Section 0: [preamble / frontmatter]
Section 1: <first heading text>
Section 2: <second heading text>
...
Section N: <last heading text>
```

Show the list to the author so they know what's coming:

> "Here are the sections in this draft:
> 0. Preamble / frontmatter
> 1. <heading 1>
> 2. <heading 2>
> ...
> N. <heading N>
>
> I'll go through each one and apply formatting, voice, and accuracy checks. Shall I start with section 0?"

Wait for a go-ahead (a "yes" or "start" is enough) before entering the section loop.

---

## Phase 5: Section-by-section revision loop

For each section in order, run all three axes, then wait for author approval before moving to the next section.

### 5a. Three-axis pass

#### Axis 1 — Formatting

Check and fix all formatting issues in the section:

- **Code line length:** Every line inside a code fence must be ≤70 characters. Use the awk check from Phase 3 (pattern 7b) for detection. Break long lines using the language's idiomatic line-continuation style (`\` for shell, intermediate variables for TypeScript/JavaScript).
- **Code fence language tags:** Every fence must have a language tag (` ```typescript `, ` ```bash `, etc.). Never leave a bare ` ``` `.
- **Dense paragraphs:** If a paragraph runs longer than ~5 sentences and enumerates distinct items, convert the items to a bulleted or numbered list. Do not list-ify flowing narrative prose.
- **Table/card candidates:** If the section compares two or more things across the same attributes, convert to an **HTML inline-styled table** — never a Markdown table. Ghost renders Markdown tables cramped (no numeric alignment, poor mobile) and won't split them into their own card; a top-level `<table>` block becomes its own clean html card. Use `width: 100%; margin: 2em 0`, header `<tr>` `border-bottom: 2px solid currentColor`, body `<tr>` `border-bottom: 1px solid rgba(128,128,128,0.25)` (dropped on the last row), cells `padding: 0.65em 1em`, numeric columns `text-align: right; font-variant-numeric: tabular-nums`. If the section has a standalone callout or tip, use a blockquote (`>`).
- **Heading style:** Headings must be sentence case — capitalize only the first word and proper nouns. No ALL-CAPS. No question-only headings (a heading ending with `?` and no declarative anchor is forbidden — rewrite as a declarative or partially declarative heading).

#### Axis 2 — Voice

Run every anti-pattern from the checklist loaded in Phase 3 against the section text:

1. Forbidden heading styles (ALL-CAPS, question-only) — already caught in Axis 1; confirm clean.
2. Editorial restatements ("in other words", "to put it simply", etc.) — delete the restatement, rewrite the original sentence.
3. Hedge words ("just", "simply", "basically", "obviously", "of course", "clearly", "needless to say") — delete and rewrite the claim more precisely.
4. AI-flavored transitions and filler phrases ("in conclusion", "it's worth noting", "delve into", "moreover,", "furthermore,", etc.) — delete and restructure.
5. Cleft and focus-frame constructions ("what this means is", "the thing about X is", "what's interesting here is") — delete the frame, state the point directly.
6. Cute closers ("happy coding", "stay curious", "hope this helps", "that's a wrap", etc.) — delete and replace with a closing line that reinforces the post's main point, poses an open question, or points to a logical next step.

For each pattern found: fix it in the section text. Do not leave anti-patterns in place and report them — repair first.

If the style guide is available, also check:
- Tone matches the author's stated adjectives.
- Sentence and paragraph rhythm matches Observed patterns.
- Vocabulary register is consistent with the style guide.

**Then read the section — don't just grep it.** The patterns above are fixed strings; the tells below are rhythm and framing, and they only surface on a read. Read the section out loud: if you wouldn't actually say a sentence, it's a tell. Fix each in place.
- **Choppy rhythm** — plain is not short; a run of short declaratives reads as mechanical. Connect them into substantive sentences that carry cause and effect, and vary length.
- **Cleft / focus-frame** — "X is what Y", "the X is that"; lead with the subject ("The skills reach Ghost through the server," not "the server is what the skills reach Ghost through").
- **Manufactured contrast** — "X is easy; Y is the hard part"; describe what actually happened instead.
- **Em-dash reveal** — "[claim] — and that turned out to be [payoff]"; drop the reveal and end on the fact.
- **Retcon** — a fix dressed up as intentional design; describe what the thing does and why, not a story of having meant it all along.
- **Overselling** — "I set one rule at the start", "the part I lean on"; understate.
- **Negative-first** — lead with the reason, not the absence ("Because a page is the same object as a post…," not "Pages don't get their own tools").

#### Axis 3 — Content and accuracy

Verify every factual claim in the section:

- **Commands and flags:** Every shell command or CLI flag must be verified against the actual tool's documentation or known behavior. Do not fabricate options. If a flag or command cannot be verified from known source (training data or a visible reference file in the project), flag it for the author: "I could not verify `--flag-name` — please confirm this is correct before publishing."
- **API names and signatures:** Every function name, method, or API reference must match the actual library version in use. If the project has a `package.json` or similar, check version constraints. If uncertain, flag it.
- **Code examples:** Every code example must compile/run correctly as written. If the section's code depends on imports or context not shown, note what is needed. Do not invent behavior.
- **URLs and references:** If the section links to an external resource, note "please verify this URL is current" — do not follow URLs or fabricate link targets.
- **Never fabricate.** If something cannot be verified from the draft context, project files, or reliable training data, flag it explicitly rather than guessing.

### 5b. Apply fixes and show a diff-style summary

After all three axes, apply the fixes to the section. Show the author a before/after summary:

> **Section <N>: <heading>**
>
> **Formatting fixes:**
> - [what was fixed, or "none"]
>
> **Voice fixes:**
> - [pattern name]: [what was fixed, or "none"]
>
> **Accuracy flags:**
> - [claim]: [verified / flagged for author confirmation]
>
> **Revised section:**
> ```markdown
> <revised section text>
> ```
>
> Approve this section, or tell me what to change.

### 5c. Wait for approval per section

Hold on the current section until the author approves it or requests changes.

- **Approved** ("looks good", "next", "approved", thumbs-up emoji, or equivalent) → write the approved section back into the draft file and advance to the next section.
- **Changes requested** → apply the author's requested changes, show the updated section, and wait for approval again. Repeat until approved.
- **Skip** ("skip this one", "leave it as-is") → leave the section unchanged in the file and advance to the next section.

After writing an approved section back to the file:

```
Edit("<drafts_dir>/<filename>.md", <old section text>, <revised section text>)
```

Then move to the next section and repeat Phase 5 from 5a.

---

## Phase 6: Final pass and hand-off

After all sections have been approved, run one final consistency check across the whole draft:

- **Heading hierarchy:** No skipped heading levels (`##` directly to `####` without `###` between).
- **Cross-section coherence:** The opening establishes the angle; the close reinforces it. If they diverged during revision, flag the mismatch.
- **Updated preamble:** If the title changed during revision, update the frontmatter `title` field to match.

All per-section `Edit()` calls in Phase 5 have persisted the approved changes to disk. The draft file is now complete with all revisions applied.

Hand off to `push-draft`:

> "All sections reviewed and approved. Draft saved to `<path>`.
>
> Run `/ghost:push-draft` to publish this draft to Ghost when you're ready."

Do not call any Ghost MCP write tools. The draft stays local until `/ghost:push-draft` handles the upload.

---

## Notes

- **Local only.** No Ghost MCP calls are made — all reads and writes target `<drafts_dir>/<filename>.md` on the local filesystem only.
- **Three axes are mandatory.** Do not skip or abbreviate any axis, even for short sections. A section that passes all three axes quickly still needs to be confirmed.
- **Accuracy axis forbids fabrication.** If a command, flag, API name, or factual claim cannot be verified, flag it to the author. Do not guess and move on.
- **Anti-patterns are inlined in Phase 3.** All checks are self-contained in this skill — no external file load required.
- **Author approval is per-section.** Never auto-advance past a section without an explicit approval signal.
- **If `ghost.local.md` is missing:** use defaults (`drafts_dir: blog-posts/drafts`, `style_guide_path: .claude/ghost-style-guide.md`) and note it.
- **Prerequisites:** `/ghost:setup-ghost` (to configure the project), `/ghost:draft-post` (to produce the draft being revised).
