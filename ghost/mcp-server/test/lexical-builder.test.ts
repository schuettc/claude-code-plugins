import { describe, it, expect } from "vitest";
import { buildLexical } from "../src/core/lexical-builder.js";

function children(r: { lexical: string }) {
  return JSON.parse(r.lexical).root.children as Array<{ type: string }>;
}

describe("buildLexical", () => {
  it("wraps a tableless post as a single markdown card", () => {
    const r = buildLexical("Just some prose.\n\nMore prose.");
    expect(r.cardCount).toBe(1);
    expect(r.cardSummary).toBe("markdown");
    expect(children(r)[0]).toMatchObject({ type: "markdown", version: 1 });
  });

  it("splits a top-level <table> into its own html card", () => {
    const md = "Intro.\n\n<table><tr><td>x</td></tr></table>\n\nOutro.";
    const r = buildLexical(md);
    expect(r.cardSummary).toBe("markdown, html, markdown");
    expect(r.cardCount).toBe(3);
  });

  it("splits prose on <!-- card --> markers", () => {
    const r = buildLexical("First.\n\n<!-- card -->\n\nSecond.");
    expect(r.cardCount).toBe(2);
    expect(r.cardSummary).toBe("markdown, markdown");
  });

  it("drops empty parts", () => {
    const r = buildLexical("<!-- card -->\n\nOnly one.");
    expect(r.cardCount).toBe(1);
  });

  it("produces a valid lexical root envelope", () => {
    const root = JSON.parse(buildLexical("Hi.").lexical).root;
    expect(root).toMatchObject({ type: "root", version: 1, indent: 0 });
  });
});
