import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Button } from "../core/Button";
import { IconButton } from "../core/IconButton";

describe("Fluer Button Component", () => {
  it("renders primary button with 10px radius styling", () => {
    const html = renderToString(<Button variant="primary">Speichern</Button>);
    expect(html).toContain("Speichern");
    expect(html).toContain("btn-fluer");
    expect(html).toContain("btn-primary");
  });

  it("renders danger button with non-solid red styling", () => {
    const html = renderToString(<Button variant="danger">Löschen</Button>);
    expect(html).toContain("Löschen");
    expect(html).toContain("btn-danger");
    // Strict Fluer constraint: never solid red block
    expect(html).not.toContain("bg-red-600");
  });

  it("renders IconButton with aria-label and 6px radius", () => {
    const html = renderToString(<IconButton icon={<span>X</span>} aria-label="Schließen" />);
    expect(html).toContain("aria-label=\"Schließen\"");
    expect(html).toContain("btn-icon");
  });
});
