# ghost-blog-mcp

A local stdio MCP server for the Ghost Admin API. Designed for the `ghost`
Claude Code plugin, but usable by any MCP client.

## Configuration

The server reads credentials from a JSON file pointed to by `GHOST_CREDENTIALS_FILE`.
The `ghost` plugin's `.mcp.json` sets this to `.claude/ghost.creds.json`, and the
`setup-ghost` skill writes the file for you. It holds:

- `GHOST_API_URL` — your Ghost site URL, e.g. `https://yourblog.ghost.io`
- `GHOST_ADMIN_API_KEY` — the Admin API Key (`id:secret`) from a Ghost custom
  integration: Ghost Admin → Settings → Advanced → Integrations → Add custom
  integration.

As a fallback, the same two values are read from environment variables of the same
name when `GHOST_CREDENTIALS_FILE` is unset.

## Run

    npx -y ghost-blog-mcp@latest

## Tools

`ghost_site_info`, `ghost_post_list`, `ghost_post_get`, `ghost_post_create`,
`ghost_post_update`, `ghost_tag_list`, `ghost_image_upload`. Posts and pages
share the post tools via a `type: post | page` argument.
