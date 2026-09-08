# Österreich-Compliance-Matrix

Diese Matrix dokumentiert den Umsetzungs-, Test- und Freigabestatus aller Anforderungen für die österreichische KMU-Compliance (GmbH/FlexCo und Einzelunternehmen) in Easy-Books.

**Status-Definitionen:**
- `not_started`: Anforderung noch nicht begonnen.
- `in_progress`: In aktiver Entwicklung.
- `verified`: Durch automatisierte Tests (Unit/Integration) auf Code-Ebene nachgewiesen.
- `blocked`: Durch externe Abhängigkeiten, fehlende Schnittstellen oder nicht freigegebene Module gesperrt.

---

## 1. Übersicht der Meilensteine und Befunde

| ID | Gegenstand / Feature | Rechtliche Grundlage | Meilenstein | Status | Zuständigkeit | Testabdeckung | Freigabedatum |
|---|---|---|---|---|---|---|---|
| **AT-01** | Unveränderliche Belege & Snapshot-Historie | § 190 Abs. 4 UGB, § 131 BAO | M1 / PR 2 | `not_started` | Core / Posting | `test_document_integrity_at.py` | – |
| **AT-02** | Rechnungslebenszyklus & Stornosicherheit | § 131 BAO, Grundsätze ordnungsmäßiger Buchführung | M1 / PR 2 | `not_started` | Core / Invoices | `test_document_integrity_at.py` | – |
| **AT-03** | Steuerbericht: Kontenauflösung & Saldierung | § 20, 21 UStG 1994 | M1 / PR 1 | `verified` | Tax / Reporting | `test_tax_reports.py` | 2026-09-08 |
| **AT-04** | Reverse Charge & EU-Leistungsbezug | § 19 Abs. 1 UStG, Art. 196 MwSt-SystRL | M3 / PR 7, 8 | `not_started` | Tax / Cross-Border | `test_at_cross_border_tax.py` | – |
| **AT-05** | AT-Steuerprofil & Steuersätze (20/13/10/4,9%) | § 10, Anlage 3 UStG 1994 | M2 / PR 4, 6 | `not_started` | Tax / Localization | `test_at_tax_treatments.py` | – |
| **AT-06** | AT-Rechnungsmerkmale & PDF-Ausgabe | § 11 UStG, § 14 UGB | M2 / PR 5 | `not_started` | Invoices / Templates | `test_at_invoice_requirements.py` | – |
| **AT-07** | Revisionssicheres Archiv & Aufbewahrung | § 132 BAO (7-jährige Aufbewahrung) | M4 / PR 14 | `not_started` | Storage / Archive | `test_at_retention.py` | – |
| **AT-08** | Periodensperre, Reopen-Historie & Abschluss | § 190, 193 UGB, BAO | M1 / PR 3 | `not_started` | Core / Periods | `test_at_period_control.py` | – |
| **AT-09** | Locale-bewusster Bank-CSV-Import & Hash-Prüfung | BAO § 131, BMF-Vorgaben | M1 / PR 1 | `verified` | Banking / Core | `test_bank_imports.py`, `test_number_parse.py` | 2026-09-08 |
| **AT-10** | UVA, U1, ZM & FinanzOnline-Export | § 21 UStG, BMF-UVA-Schnittstelle | M3 / PR 10 | `not_started` | Tax / Reporting | `test_at_uva.py`, `test_at_zm.py` | – |
| **AT-11** | UGB-Bilanz/GuV (§ 224/231 UGB) & E1a E/A-Rechnung | § 4 Abs. 3 EStG, § 224, 231 UGB | M4 / PR 11, 12 | `not_started` | Financials / Reporting | `test_at_ugb_statements.py`, `test_at_ear.py` | – |
| **AT-12** | Österreichische Anlagenbuchhaltung & Halbjahres-AfA | § 7, 8 EStG 1988, § 203 UGB | M4 / PR 13 | `not_started` | Assets / Depreciation | `test_at_depreciation.py` | – |
| **AT-13** | Registrierkasse / RKSV & Datenerfassungsprotokoll | RKSV, § 131b BAO | M5 / PR 16 | `blocked` | POS / RKSV | `test_at_rksv.py` | – |
| **AT-14** | Personalverrechnung (Lohnkonto, Abgaben) | ASVG, EStG, FLAG | M5 / PR 18 | `blocked` | Payroll / HR | `test_at_payroll.py` | – |
| **AT-15** | Sprache de-AT, Zahlen-/Währungsformate & Basiswährung | UGB, BAO | M2 / PR 4 | `in_progress` | Frontend / Core | `test_number_parse.py` | – |

---

## 2. Detaillierte Capabilities nach Freigabeprofil

### Profil `AT-UGB-VAT` (GmbH, FlexCo, bilanzierungspflichtig)
- Doppelte Buchführung nach UGB: `in_progress` (Kontenplan & Gliederung ausstehend in PR 4 & 11)
- Akute Rechenintegrität (Konto 1200 / Vorsteuer / Saldierung): `verified` (PR 1)
- Bank-Statement-Import (österreichische Formate, z. B. Erste Bank, Raiffeisen): `verified` (PR 1)
- Unveränderliche Belege & Periodensperre: `not_started` (PR 2, 3)
- UVA-Auswertung & ZM: `not_started` (PR 10)
- UGB-Bilanz/GuV (§ 224, 231 UGB): `not_started` (PR 11)
- KSt-Arbeitsblatt (23 % KSt): `verified` (PR 1)

### Profil `AT-EAR-VAT` (Einzelunternehmen mit USt)
- Einnahmen-Ausgaben-Rechnung nach Zufluss-/Abflussprinzip: `not_started` (PR 12)
- Bank-Statement-Import: `verified` (PR 1)
- Wareneingangsbuch & Anlagenverzeichnis: `not_started` (PR 12)
- Steuerberichte & Vorsteuerermittlung: `verified` (PR 1)

### Profil `AT-EAR-KU` (Kleinunternehmer nach § 6 Abs. 1 Z 27 UStG)
- Schwellenwert-Überwachung (55.000 € / 10 % Toleranz): `not_started` (PR 9)
- Steuerfreie Rechnungen mit Pflichtangabe: `not_started` (PR 9)
- RC-/Erwerbsteuer-Behandlung für Kleinunternehmer: `not_started` (PR 9)

### Bedingte Module (vorerst für AT serverseitig gesperrt)
- `AT-RKSV`: Registrierkassensicherheitsverordnung mit DEP & Signaturkarte/Cloud-HSM (`blocked` bis PR 16)
- `AT-ERB`: e-Rechnung.gv.at / ebInterface / Peppol BIS (`blocked` bis PR 17)
- `AT-PAYROLL`: Österreichische Lohnabrechnung (`blocked` bis PR 18)

---

## 3. Historie der Verifikationen

| Datum | PR / Commit | Geprüfte Komponenten | Prüfergebnis |
|---|---|---|---|
| **2026-09-08** | PR 1 | `backend/services/number_parse.py`, `backend/routers/bank_imports.py`, `backend/routers/reports.py` | **26/26 Tests bestanden** (100 % grün auf `test_tax_reports.py`, `test_bank_imports.py`, `test_number_parse.py`, `test_tax_engine.py`) |
