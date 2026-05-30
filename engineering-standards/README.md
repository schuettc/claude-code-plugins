# engineering-standards

Evergreen engineering standards — the conventions I hold code to *throughout* a project's life, not just when standing it up. These are pure **advisory** skills: they carry no tooling and no setup steps, they fire on their own when the situation matches, and they're safe to leave enabled forever.

This is the deliberate counterpart to `project-workflow`: that plugin is one-shot *setup* (disposable once a repo is stood up); this one is the *standards you keep consulting* long after. Splitting them means you can disable the setup plugin without losing the evergreen guidance.

## Skills

- **`project-structure`** — how a repo is laid out and how files/modules are named, so every project looks the same and generated code has an obvious right place. Feature-colocation over type-folders, one-module-one-responsibility, no `utils`/`misc` junk drawers. The judgment-layer counterpart to the mechanical guardrails (skylos/fallow catch dead code & complexity; this catches *placement & organization*, which tools can't judge). Directly serves the "all our projects look the same" goal.
- **`github-api-discipline`** — for build/deploy/background code that reads from another GitHub repo at runtime: one bulk fetch per repo (zipball/tarball), honor `retry-after` / `x-ratelimit-reset`, share fetched content, authenticate with an App installation token. Saved after blowing the App installation's 15000/hr quota mid-promotion. Ships the reference fetcher + backoff helper under `templates/github-rate-limit/`.

## Backlog (evergreen standards to add here)

These were captured as project-workflow backlog but belong here — they're consulted during ongoing work, not setup:

- **GitHub App vs PAT for automation** — when to use which, the 15000/hr installation quota math, the "PAT shares the user's 5000/hr with chat sessions" gotcha.
- **`LEFTHOOK_EXCLUDE` documented operator-skip pattern** — when a hook escape is legitimate vs. `--no-verify` smuggling.
- **Secrets-manager + shared installation token** — the LWC pattern (`LwcSharedGitHubApp-{Env}` with App ID + installation ID + PKCS#8 key; bootstrap script).

## Conventions

All skills here are advisory (no `user-invocable`, no commands) — they're consulted when their described situation arises. New ones get descriptive names (the same ambient-skill style as `feature-workflow`'s `guarding-scope` / `auditing-context`). Each leads with the **rule**, then the **why** (a real incident or working setup), then **how to apply**.
