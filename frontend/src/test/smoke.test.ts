import { describe, it, expect } from "vitest";

describe("smoke test", () => {
  it("vitest is working", () => {
    expect(1 + 1).toBe(2);
  });

  it("import.meta.env is available", () => {
    expect(import.meta.env).toBeDefined();
    expect(typeof import.meta.env.MODE).toBe("string");
  });
});
