import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { lockTourScroll, restoreTourScroll } from "./product-experience";

describe("tour scroll lock", () => {
  const previousDocument = globalThis.document;

  beforeEach(() => {
    Object.defineProperty(globalThis, "document", {
      value: {
        documentElement: {
          classList: { add: vi.fn(), remove: vi.fn() },
          style: { overflow: "auto", scrollBehavior: "smooth" },
        },
        body: { style: { overflow: "scroll", paddingRight: "12px", paddingBottom: "18px" } },
      },
      configurable: true,
      writable: true,
    });
  });

  afterEach(() => {
    if (previousDocument === undefined) {
      Reflect.deleteProperty(globalThis as typeof globalThis & { document?: Document }, "document");
      return;
    }

    Object.defineProperty(globalThis, "document", {
      value: previousDocument,
      configurable: true,
      writable: true,
    });
  });

  it("restores the original page scroll state after the guide closes", () => {
    const root = document.documentElement;
    const body = document.body;

    root.style.overflow = "auto";
    root.style.scrollBehavior = "smooth";
    body.style.overflow = "scroll";
    body.style.paddingRight = "12px";
    body.style.paddingBottom = "18px";

    lockTourScroll();

    expect(root.classList.add).toHaveBeenCalledWith("tour-scroll-lock");
    expect(root.style.overflow).toBe("auto");
    expect(root.style.scrollBehavior).toBe("auto");
    expect(body.style.overflow).toBe("scroll");
    expect(body.style.paddingRight).toBe("12px");
    expect(body.style.paddingBottom).toBe("18px");

    restoreTourScroll();

    expect(root.classList.remove).toHaveBeenCalledWith("tour-scroll-lock");
    expect(root.style.overflow).toBe("auto");
    expect(root.style.scrollBehavior).toBe("");
    expect(body.style.overflow).toBe("scroll");
    expect(body.style.paddingRight).toBe("12px");
    expect(body.style.paddingBottom).toBe("18px");
  });
});
