// Strip a leading YAML frontmatter block (--- ... ---) if present.
export function stripFrontmatter(md: string): string {
  return md.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n+/, "");
}

// Strip a leading H1 line — Ghost owns the title, so an H1 in the body
// would render as duplicate literal text.
export function stripLeadingH1(md: string): string {
  return md.replace(/^# .+\r?\n\r?\n?/, "");
}
