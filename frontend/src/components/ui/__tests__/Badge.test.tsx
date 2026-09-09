import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Badge } from "../core/Badge";
import { Tag } from "../core/Tag";

describe("Fluer Badge and Tag", () => {
  it("renders badge with 3px radius and optional dot", () => {
    const html = renderToString(<Badge tone="success" dot>Gebucht</Badge>);
    expect(html).toContain("Gebucht");
    expect(html).toContain("badge-fluer");
    expect(html).toContain("badge-success");
    expect(html).toContain("badge-dot");
  });

  it("renders tag with 999px pill radius", () => {
    const html = renderToString(<Tag>Kategorie A</Tag>);
    expect(html).toContain("Kategorie A");
    expect(html).toContain("tag-fluer");
  });
});
