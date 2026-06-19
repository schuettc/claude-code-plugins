import { describe, it, expect } from "vitest";
import { loadConfig, GhostConfigError } from "../src/config.js";

const VALID = {
  GHOST_API_URL: "https://example.ghost.io",
  GHOST_ADMIN_API_KEY: "64ab12cd34ef:0011223344556677889900aabbccddee",
};

describe("loadConfig", () => {
  it("returns config from valid env", () => {
    expect(loadConfig(VALID)).toEqual({
      url: "https://example.ghost.io",
      adminKey: "64ab12cd34ef:0011223344556677889900aabbccddee",
    });
  });

  it("throws GhostConfigError naming setup-ghost when the key is missing", () => {
    expect(() => loadConfig({ GHOST_API_URL: VALID.GHOST_API_URL })).toThrow(
      GhostConfigError,
    );
    expect(() => loadConfig({ GHOST_API_URL: VALID.GHOST_API_URL })).toThrow(
      /setup-ghost/,
    );
  });

  it("throws on a non-http url", () => {
    expect(() =>
      loadConfig({ ...VALID, GHOST_API_URL: "example.ghost.io" }),
    ).toThrow(GhostConfigError);
  });

  it("throws on a malformed admin key", () => {
    expect(() =>
      loadConfig({ ...VALID, GHOST_ADMIN_API_KEY: "not-a-key" }),
    ).toThrow(GhostConfigError);
  });
});
