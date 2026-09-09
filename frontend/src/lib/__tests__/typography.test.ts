import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

describe("Typography Setup", () => {
  it("defines Geist font variables in layout.tsx or globals.css", () => {
    const layoutPath = path.resolve(__dirname, "../../app/layout.tsx");
    const globalsPath = path.resolve(__dirname, "../../app/globals.css");
    const layoutContent = fs.readFileSync(layoutPath, "utf8");
    const globalsContent = fs.readFileSync(globalsPath, "utf8");

    const hasGeistInLayout = layoutContent.includes("Geist") || layoutContent.includes("geist");
    const hasGeistInGlobals = globalsContent.includes("Geist") || globalsContent.includes("--font-sans");
    expect(hasGeistInLayout || hasGeistInGlobals).toBe(true);
  });
});
