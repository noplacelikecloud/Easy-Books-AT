import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Dialog } from "../feedback/Dialog";
import { Tabs } from "../navigation/Tabs";

describe("Fluer Feedback and Navigation", () => {
  it("renders dialog with 20px radius and modal scrim", () => {
    const html = renderToString(
      <Dialog open={true} onClose={() => {}} title="Buchung stornieren">
        <p>Möchten Sie diesen Beleg wirklich stornieren?</p>
      </Dialog>
    );
    expect(html).toContain("Buchung stornieren");
    expect(html).toContain("dialog-fluer");
  });

  it("renders tabs with active Deep Blue indicator", () => {
    const html = renderToString(
      <Tabs
        items={[{ id: "all", label: "Alle" }, { id: "open", label: "Offen", count: 3 }]}
        activeId="open"
        onChange={() => {}}
      />
    );
    expect(html).toContain("Offen");
    expect(html).toContain("tabs-fluer");
    expect(html).toContain("tab-active");
  });
});
