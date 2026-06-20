import { describe, it, expect } from "vitest";
import { stripFrontmatter, stripLeadingH1 } from "../src/core/markdown.js";

describe("stripFrontmatter", () => {
  it("removes a leading YAML frontmatter block", () => {
    const md = "---\ntitle: Hi\nslug: hi\n---\n\nBody text.";
    expect(stripFrontmatter(md)).toBe("Body text.");
  });

  it("leaves content without frontmatter untouched", () => {
    expect(stripFrontmatter("# Title\n\nBody.")).toBe("# Title\n\nBody.");
  });
});

describe("stripLeadingH1", () => {
  it("removes a leading H1 line", () => {
    expect(stripLeadingH1("# Title\n\nBody.")).toBe("Body.");
  });

  it("does not remove an H2 or mid-document H1", () => {
    expect(stripLeadingH1("## Sub\n\nBody.")).toBe("## Sub\n\nBody.");
  });
});
