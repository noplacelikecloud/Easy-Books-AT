import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Input } from "../forms/Input";
import { Select } from "../forms/Select";
import { Checkbox } from "../forms/Checkbox";
import { Switch } from "../forms/Switch";

describe("Fluer Form Controls", () => {
  it("renders input with label and error state", () => {
    const html = renderToString(<Input label="E-Mail" error="Ungültige Adresse" />);
    expect(html).toContain("E-Mail");
    expect(html).toContain("Ungültige Adresse");
    expect(html).toContain("input-fluer");
  });

  it("renders select with chevron indicator", () => {
    const html = renderToString(
      <Select label="Konto" options={[{ value: "1000", label: "1000 Kassa" }]} />
    );
    expect(html).toContain("1000 Kassa");
    expect(html).toContain("select-fluer");
  });

  it("renders checkbox with 3px radius", () => {
    const html = renderToString(<Checkbox label="Aktiviert" defaultChecked />);
    expect(html).toContain("checkbox-fluer");
  });

  it("renders switch toggle with pill radius", () => {
    const html = renderToString(<Switch checked={true} onChange={() => {}} label="Automatik" />);
    expect(html).toContain("switch-fluer");
  });
});
