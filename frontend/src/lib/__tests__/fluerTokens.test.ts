import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

describe("Fluer Design Tokens", () => {
  const cssPath = path.resolve(__dirname, "../../app/globals.css");
  const css = fs.readFileSync(cssPath, "utf8");

  it("defines Fluer neutrals scale", () => {
    expect(css).toContain("--n-0:");
    expect(css).toContain("--n-25:");
    expect(css).toContain("--n-100:");
    expect(css).toContain("--n-900:");
  });

  it("defines Fluer primary Deep Blue palette", () => {
    expect(css).toContain("--blue-500: #17518c");
    expect(css).toContain("--blue-600: #123d6a");
  });

  it("defines strict Fluer radii scale", () => {
    expect(css).toMatch(/--radius-xs:\s*3px/);
    expect(css).toMatch(/--radius-sm:\s*6px/);
    expect(css).toMatch(/--radius-md:\s*10px/);
    expect(css).toMatch(/--radius-lg:\s*14px/);
    expect(css).toMatch(/--radius-xl:\s*20px/);
    expect(css).toMatch(/--radius-pill:\s*999px/);
  });

  it("defines Fluer Dark Mode tokens", () => {
    expect(css).toContain('[data-theme="dark"]');
    expect(css).toContain("--bg-page:        var(--n-900)");
  });
});
