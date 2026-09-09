import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Card } from "../core/Card";

describe("Fluer Card Component", () => {
  it("renders card with 14px radius and header", () => {
    const html = renderToString(
      <Card title="Umsatzübersicht" subtitle="Laufendes Geschäftsjahr">
        <div>Inhalt</div>
      </Card>
    );
    expect(html).toContain("Umsatzübersicht");
    expect(html).toContain("Laufendes Geschäftsjahr");
    expect(html).toContain("card-fluer");
  });

  it("renders sunken card for grouped sections", () => {
    const html = renderToString(
      <Card tone="sunken">
        <div>Details</div>
      </Card>
    );
    expect(html).toContain("card-sunken");
  });
});
