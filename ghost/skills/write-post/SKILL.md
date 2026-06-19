---
name: write-post
description: Use to write a Ghost blog post end to end, walking the full plan→draft→revise→push flow in one guided pass. Triggers on "write a post about X end to end", "take this from idea to a ghost draft", "guide me through writing a post".
---

# Write a Ghost blog post end to end

You are the guided entry point for the full ghost blog workflow. You do not re-implement any sub-skill logic — you orchestrate `draft-post` → `revise-post` → `push-draft` in order, stopping at draft-in-Ghost. Work through each gate in sequence.

The discrete skills remain usable à la carte: if the author already has a draft they want to revise, they can invoke `/ghost:revise-post` directly; if they have a revised draft ready to push, they can invoke `/ghost:push-draft` directly. This skill is the guided full run — useful when starting from a topic and wanting a single coordinated session.

---

## Gate 1: Preflight — setup

Check whether Ghost credentials are verified by calling:

```
ghost_site_info()
```

**If the call succeeds** — the Ghost connection is live and credentials are valid. Proceed to Gate 2.

**If the call fails (auth error, connection refused, tool unavailable)** — setup is incomplete. Route the author to `setup-ghost`:

> "The Ghost connection isn't verified. Let's get that sorted first.
>
> Run `/ghost:setup-ghost` to configure your Admin API key and verify the connection, then come back here."

Stop here until setup is confirmed working.

---

## Gate 2: Preflight — style guide

Read `.claude/ghost.local.md` to find `style_guide_path`:

```
Read(".claude/ghost.local.md")
```

Extract `style_guide_path` (default `.claude/ghost-style-guide.md` if the file is missing or the field is absent).

Then check whether the style guide exists:

```
Read("<style_guide_path>")
```

**If the style guide exists and is non-empty** — proceed to Phase 1.

**If the style guide is missing or empty** — determine which path fits:

- **If the author's Ghost site has published posts** (or they say they do), route to `build-style-guide`:

  > "No style guide found at `<style_guide_path>`. Since your site has published posts, I'll extract your voice from those.
  >
  > Run `/ghost:build-style-guide` to generate it, then return here and I'll continue."

- **If the author is starting from a blank slate** (no existing posts, brand-new site), route to `define-voice` first:

  > "No style guide found and you're starting fresh. Let's define your writing voice first.
  >
  > Run `/ghost:define-voice` to capture your voice preferences, then `/ghost:build-style-guide` to produce the style guide, then return here."

If you cannot determine which case applies, ask:

> "Is your Ghost site new (no published posts yet), or do you have existing published posts I should learn from?"

Stop here until a style guide exists at `style_guide_path`.

---

## Phase 1: Draft

Invoke `draft-post` to plan and write the first full draft:

> "Preflight complete. Let's start with the draft.
>
> I'll walk you through `/ghost:draft-post` now — this covers the angle, outline, and first full draft written to your local `drafts_dir`, followed by a self-audit pass."

Hand control to `/ghost:draft-post`. Let it run to completion (through its Phase 6 hand-off message) before continuing.

When `draft-post` completes, note the local draft path it reports.

---

## Phase 2: Revise

Once the draft is written, hand off to `revise-post` for the interactive section-by-section review:

> "Draft is ready. Moving to revision.
>
> I'll walk you through `/ghost:revise-post` now — we'll go section by section, applying formatting, voice, and accuracy checks. Confirm each section before we advance."

Hand control to `/ghost:revise-post`. Let it run to completion (through its Phase 6 hand-off message) before continuing.

---

## Phase 3: Push as a draft

Once revision is complete and the author has approved the final draft, push to Ghost:

> "Revision complete. Ready to push to Ghost as a draft.
>
> I'll hand off to `/ghost:push-draft` now — this uploads the draft to Ghost, verifies the card structure and links, and returns the Ghost editor URL for your final review before publishing."

Hand control to `/ghost:push-draft`. Let it run to completion.

---

## Completion

After `push-draft` returns the editor URL, confirm the workflow is done:

> "All done. The post is in Ghost as a draft — use the editor URL above to review and publish when you're ready.
>
> The workflow stops here. Publishing is always done through the Ghost UI."

This skill never publishes or schedules. The draft-only invariant from `push-draft` carries end to end.

---

## Notes

- **Thin orchestrator.** This skill sequences the three sub-skills; all logic lives in them. Do not duplicate their phase content here.
- **Draft-only invariant.** `push-draft` enforces `status: draft` on every push — this skill never overrides or bypasses that guarantee.
- **À-la-carte use.** The sub-skills are fully self-contained and can be invoked directly at any point in the process. `write-post` is the guided on-ramp, not a gatekeeper.
- **Preflight is non-negotiable.** A missing style guide or broken Ghost connection will produce a poor result downstream. Always resolve Gate 1 and Gate 2 before drafting.
- **If `ghost.local.md` is missing:** use the default `style_guide_path` of `.claude/ghost-style-guide.md` and note it to the author.
- **Prerequisites:** `/ghost:setup-ghost` (verified Ghost connection), `/ghost:define-voice` and/or `/ghost:build-style-guide` (style guide at `style_guide_path`).
