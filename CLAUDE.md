# claude-code-plugins

## Plugin authoring

Plugins are skills-only: no `commands/` directory and no `commands` key. Name invocable actions `<domain>-<verb>` with `user-invocable: true`; give ambient advisory skills a descriptive name with no prefix. Name a plugin `<domain>-<category-noun>`. Per-project disable goes through `enabledPlugins`; setup skills offer `/plugin disable` and never self-mutate. Mirror `feature-workflow` when adding a plugin. How plugins compose is in [ADOPTION.md](ADOPTION.md).

## Publishing npm packages

Packages published through npm OIDC trusted publishing must set `repository.url` (plus `repository.directory` in a monorepo) to the building repo, or the registry rejects provenance with a 422. Publish a prerelease to the `dev` tag first; promoting to `latest` is a deliberate step (tag a clean version, see `.github/workflows/publish-ghost-mcp-dev.yml`). Never reuse a version after a failed publish. Test an npm `bin` entry point by spawning it through a symlink, the way npm installs it.
