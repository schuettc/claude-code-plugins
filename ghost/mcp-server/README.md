# ghost-mcp

A local stdio MCP server for the Ghost Admin API. Designed for the `ghost`
Claude Code plugin, but usable by any MCP client.

## Configuration

Set two environment variables (the `setup-ghost` skill automates this):

- `GHOST_API_URL` — your Ghost site URL, e.g. `https://yourblog.ghost.io`
- `GHOST_ADMIN_API_KEY` — the Admin API Key (`id:secret`) from a Ghost custom
  integration: Ghost Admin → Settings → Advanced → Integrations → Add custom
  integration.

## Run

    npx -y ghost-blog-mcp@latest

## Tools

`ghost_site_info`, `ghost_post_list`, `ghost_post_get`, `ghost_post_create`,
`ghost_post_update`, `ghost_tag_list`, `ghost_image_upload`. Posts and pages
share the post tools via a `type: post | page` argument.
