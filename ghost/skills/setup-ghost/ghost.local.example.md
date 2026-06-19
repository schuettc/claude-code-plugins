---
# Ghost plugin per-project config (non-secret). Copy to .claude/ghost.local.md.
# Secrets (GHOST_API_URL, GHOST_ADMIN_API_KEY) go in .claude/settings.local.json, NOT here.
corpus_filter: "status:published"   # NQL filter for the voice-learning corpus
corpus_limit: 25                     # how many recent posts to learn from
style_guide_path: ".claude/ghost-style-guide.md"
drafts_dir: "blog-posts/drafts"      # where local draft .md files live
default_tags: []                     # tags every post gets, e.g. ["early-access"]
default_visibility: "public"         # public | members | paid
early_access:                        # optional paywall pattern; omit to disable
  enabled: false
  tag: "early-access"
  visibility: "paid"
---

# Ghost project config

Human-readable notes about this site's writing setup. The frontmatter above is
what the skills read; this body is for your own reference.
