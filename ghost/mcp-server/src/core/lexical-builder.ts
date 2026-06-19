export interface LexicalResult {
  lexical: string;
  cardSummary: string;
  cardCount: number;
}

interface Part {
  type: "markdown" | "html";
  content: string;
}

const TABLE_RE = /<table[\s\S]*?<\/table>/g;
const CARD_MARKER = "<!-- card -->";

// Split markdown into Ghost lexical cards. Top-level <table> blocks become
// their own `html` cards (preserving inline styling and keeping each prose
// chunk between tables independently editable in the Ghost UI); the prose
// between them is further split on explicit <!-- card --> markers. Without
// either boundary, the whole post is one markdown card.
export function buildLexical(markdown: string): LexicalResult {
  const parts: Part[] = [];
  let lastIndex = 0;
  let m: RegExpExecArray | null;
  TABLE_RE.lastIndex = 0;

  while ((m = TABLE_RE.exec(markdown)) !== null) {
    pushMarkdownParts(parts, markdown.slice(lastIndex, m.index));
    parts.push({ type: "html", content: m[0] });
    lastIndex = m.index + m[0].length;
  }
  pushMarkdownParts(parts, markdown.slice(lastIndex));

  const children = parts
    .filter((p) => p.content.trim().length > 0)
    .map((p) =>
      p.type === "markdown"
        ? { type: "markdown", version: 1, markdown: p.content.trim() }
        : { type: "html", version: 1, html: p.content.trim() },
    );

  const lexical = JSON.stringify({
    root: {
      children,
      direction: null,
      format: "",
      indent: 0,
      type: "root",
      version: 1,
    },
  });

  return {
    lexical,
    cardSummary: children.map((c) => c.type).join(", "),
    cardCount: children.length,
  };
}

function pushMarkdownParts(parts: Part[], chunk: string): void {
  if (!chunk) return;
  for (const piece of chunk.split(CARD_MARKER)) {
    parts.push({ type: "markdown", content: piece });
  }
}
