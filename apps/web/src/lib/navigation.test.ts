import { describe, expect, it } from "vitest";

import { navigationItems } from "./navigation";

describe("primary navigation", () => {
  it("exposes every product route exactly once", () => {
    expect(navigationItems.map((item) => item.href)).toEqual([
      "/dashboard",
      "/discover",
      "/opportunities",
      "/distributions",
      "/functions",
      "/settings",
    ]);
    expect(new Set(navigationItems.map((item) => item.href)).size).toBe(navigationItems.length);
  });
});
