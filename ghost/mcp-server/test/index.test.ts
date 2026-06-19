import { describe, it, expect, vi } from "vitest";
import { buildClient } from "../src/index.js";

const VALID = {
  GHOST_API_URL: "https://example.ghost.io",
  GHOST_ADMIN_API_KEY:
    "0123456789abcdef01234567:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
};

describe("buildClient (startup env handling)", () => {
  it("falls back to an unconfigured client (no exit) when creds are missing, logging setup-ghost", async () => {
    const err = vi.spyOn(console, "error").mockImplementation(() => {});
    const client = buildClient({});
    // Logs an actionable message to stderr...
    expect(err).toHaveBeenCalledWith(expect.stringContaining("setup-ghost"));
    // ...and every operation rejects with that message, so tools surface a
    // diagnosable error rather than the server hard-exiting into an opaque
    // "-32000 connection closed".
    await expect(client.siteInfo()).rejects.toThrow(
      /setup-ghost|Ghost credentials/,
    );
    err.mockRestore();
  });

  it("builds a configured client from valid env", () => {
    const client = buildClient(VALID);
    expect(typeof client.siteInfo).toBe("function");
    expect(client.baseUrl).toBe("https://example.ghost.io");
  });
});
