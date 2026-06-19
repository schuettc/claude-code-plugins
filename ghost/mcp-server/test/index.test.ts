import { describe, it, expect, vi } from "vitest";

describe("main env validation", () => {
  it("exits non-zero with an actionable message when the key is missing", async () => {
    const err = vi.spyOn(console, "error").mockImplementation(() => {});
    const exit = vi.spyOn(process, "exit").mockImplementation(((): never => {
      throw new Error("exited");
    }) as never);
    const { main } = await import("../src/index.js");
    await expect(main({})).rejects.toThrow("exited");
    expect(err).toHaveBeenCalledWith(expect.stringContaining("setup-ghost"));
    expect(exit).toHaveBeenCalledWith(1);
    err.mockRestore();
    exit.mockRestore();
  });
});
