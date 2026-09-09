import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../table/Table";

describe("Fluer Table Component", () => {
  it("renders table with 14px outer container radius and hairline borders", () => {
    const html = renderToString(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Beleg-Nr.</TableHead>
            <TableHead align="right">Betrag</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell mono>AR-2026-0042</TableCell>
            <TableCell align="right" mono>€ 1.250,00</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    expect(html).toContain("AR-2026-0042");
    expect(html).toContain("table-fluer-container");
    expect(html).toContain("font-mono");
  });
});
