import { describe, expect, it } from "vitest";

import { navigationItems } from "./navigation";

describe("primary navigation", () => {
  it("exposes every product route exactly once", () => {
    expect(navigationItems.map((item) => item.href)).toEqual([
      "/dashboard",
      "/discover",
      "/opportunities",
      "/distributions",
      "/monitoring",
      "/settings",
    ]);
    expect(new Set(navigationItems.map((item) => item.href)).size).toBe(navigationItems.length);
  });

  it("keeps analytical labs inside the advanced workspace", () => {
    expect(navigationItems.filter((item) => item.level === "advanced").map((item) => item.href)).toEqual([
      "/distributions",
      "/monitoring",
    ]);
  });
});
