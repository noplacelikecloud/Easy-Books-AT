# Österreich-Compliance-Matrix

Diese Matrix dokumentiert den Umsetzungs-, Test- und Freigabestatus aller Anforderungen für die österreichische KMU-Compliance (GmbH/FlexCo und Einzelunternehmen) in Easy-Books.

**Status-Definitionen:**
- `not_started`: Anforderung noch nicht begonnen.
- `in_progress`: In aktiver Entwicklung.
- `verified`: Durch automatisierte Tests (Unit/Integration) auf Code-Ebene nachgewiesen.
- `blocked`: Durch externe Abhängigkeiten, fehlende Schnittstellen oder nicht freigegebene Module gesperrt (serverseitig durch Capability-Gates technisch erzwungen).

---

## 1. Übersicht der Meilensteine und Befunde

| ID | Gegenstand / Feature | Rechtliche Grundlage | Meilenstein | Status | Zuständigkeit | Testabdeckung | Freigabedatum |
|---|---|---|---|---|---|---|---|
| **AT-01** | Unveränderliche Belege & Snapshot-Historie | § 190 Abs. 4 UGB, § 131 BAO | M1 / PR 2 | `verified` | Core / Posting | `test_document_integrity_at.py` | 2026-09-08 |
| **AT-02** | Rechnungslebenszyklus & Stornosicherheit | § 131 BAO, GoB | M1 / PR 2 | `verified` | Core / Invoices | `test_document_integrity_at.py`, `test_at_tax_events.py` | 2026-09-08 |
| **AT-03** | Steuerbericht: Kontenauflösung & Saldierung | § 20, 21 UStG 1994 | M1 / PR 1 | `verified` | Tax / Reporting | `test_tax_reports.py`, `test_at_tax_reconciliation.py` | 2026-09-08 |
| **AT-04** | Reverse Charge & EU-Leistungsbezug | § 19 Abs. 1 UStG, Art. 196 MwSt-SystRL | M3 / PR 7, 8 | `in_progress` | Tax / Cross-Border | `test_at_cross_border_tax.py`, `test_at_tax_treatments.py` | — |
| **AT-05** | AT-Steuerprofil & Steuersätze (20/13/10/4,9%) | § 10, Anlage 3 UStG 1994 | M2 / PR 4, 6 | `verified` | Tax / Localization | `test_at_tax_treatments.py`, `test_at_profile.py` | 2026-09-08 |
| **AT-06** | AT-Rechnungsmerkmale & PDF-Ausgabe | § 11 UStG, § 14 UGB | M2 / PR 5 | `verified` | Invoices / Templates | `test_at_invoice_requirements.py` | 2026-09-08 |
| **AT-07** | Revisionssicheres Archiv & Aufbewahrung | § 132 BAO (7-jährige Aufbewahrung) | M4 / PR 14 | `in_progress` | Storage / Archive | `test_at_retention.py`, `test_at_accountant_export.py` | — |
| **AT-08** | Periodensperre, Reopen-Historie & Abschluss | § 190, 193 UGB, BAO | M1 / PR 3 | `verified` | Core / Periods | `test_at_period_control.py` | 2026-09-08 |
| **AT-09** | Locale-bewusster Bank-CSV-Import & Hash-Prüfung | BAO § 131, BMF-Vorgaben | M1 / PR 1 | `verified` | Banking / Core | `test_bank_imports.py`, `test_number_parse.py` | 2026-09-08 |
| **AT-10** | UVA, U1, ZM & FinanzOnline-Export | § 21 UStG, BMF-UVA-Schnittstelle | M3 / PR 10 | `verified` | Tax / Reporting | `test_at_uva.py`, `test_at_zm.py`, `test_at_tax_reconciliation.py` | 2026-09-08 |
| **AT-11** | UGB-Bilanz/GuV (§ 224/231 UGB) & E1a E/A-Rechnung | § 4 Abs. 3 EStG, § 224, 231 UGB | M4 / PR 11, 12 | `in_progress` | Financials / Reporting | `test_at_ugb_statements.py`, `test_at_ear.py` | — |
| **AT-12** | Österreichische Anlagenbuchhaltung & Halbjahres-AfA | § 7, 8, 13 EStG 1988, § 203 UGB | M4 / PR 13 | `in_progress` | Assets / Depreciation | `test_at_depreciation.py` | — |
| **AT-13** | Registrierkasse / RKSV & Datenerfassungsprotokoll | RKSV, § 131b BAO | M5 / PR 16 | `blocked` | POS / RKSV | `test_at_conditional_modules.py` | 2026-09-08 |
| **AT-14** | Personalverrechnung (Lohnkonto, Abgaben) | ASVG, EStG, FLAG | M5 / PR 18 | `blocked` | Payroll / HR | `test_at_conditional_modules.py` | 2026-09-08 |
| **AT-15** | Sprache de-AT, Zahlen-/Währungsformate & Basiswährung | UGB, BAO | M2 / PR 4 | `verified` | Frontend / Core | `test_number_parse.py`, `test_at_profile.py` | 2026-09-08 |
| **AT-16** | Bundese-Rechnung / e-Rechnung.gv.at | BVergG, IKTKonG, ebInterface/Peppol-Vorgaben | M5 / PR 17 | `blocked` | eInvoice / Integration | `test_at_conditional_modules.py` | — |

---

## 2. Detaillierte Capabilities nach Freigabeprofil

### Profil `AT-UGB-VAT` (GmbH, FlexCo, bilanzierungspflichtig)
- Doppelte Buchführung nach UGB (§§ 224, 231 UGB): `verified` (PR 4, 11)
- Akute Rechenintegrität (Konto 1200 / Vorsteuer / Saldierung): `verified` (PR 1)
- Bank-Statement-Import (österreichische Formate, z. B. Erste Bank, Raiffeisen): `verified` (PR 1)
- Unveränderliche Belege, Rechnungs-Snapshots & Stornosicherheit: `verified` (PR 2)
- Periodensperre, Reopen-Audit & Jahresabschlussbuchungen: `verified` (PR 3)
- Semantische Kontenrollen (`AccountRoleBinding`): `verified` (PR 4)
- UVA-Auswertung (U30 XML, Kennzahlen gem. BMF), ZM (FinanzOnline XML) & U1 2025: `verified` für lokalen Export (PR 10)
- Drei-Wege-Steuerabstimmung (GL ↔ TaxEvent ↔ UVA): `verified` (PR 10)
- UGB-Bilanz/GuV (§§ 224, 231 UGB) mit Eigenkapitalfehlbetrag-Ausweis (§ 225 Abs. 1 UGB): `in_progress` bis zum vollständigen Mapping-Assistenten (PR 11)
- Anlagenverzeichnis, Halbjahres-AfA & GWG (1.000 € Grenzwert): `in_progress` bis zu Abgang/Sonderfällen und Doppelbasis (PR 13)
- Wareneingangsbuch (§ 127 BAO) & Prüfexport: `verified` für die vorhandenen Kernabläufe (PR 14)
- Revisionssicheres Archiv (7-jährige Aufbewahrung gem. § 132 BAO, Legal Hold): `in_progress` bis zum Restore-Nachweis (PR 14)
- KSt-Arbeitsblatt (23 % KSt, Mehr-/Weniger-Rechnung, Mindest-KSt): `verified` (PR 15)
- Generischer Kanzlei-Prüfexport mit SHA-256 Manifest: `verified` (PR 15)

### Profil `AT-EAR-VAT` (Einzelunternehmen mit USt)
- Einnahmen-Ausgaben-Rechnung nach Zufluss-/Abflussprinzip (§ 19 EStG): `verified` für Rechnungszahlungen und direkte Bar-/Bankbelege (PR 12)
- Formular E1a-2025 Zuordnung & Kennzahlen: `in_progress` für zusätzliche Sonderklassifikationen (PR 12)
- Bank-Statement-Import mit Hash-Prüfung: `verified` (PR 1)
- Wareneingangsbuch (§ 127 BAO) mit fortlaufender Nummerierung: `verified` (PR 14)
- Anlagenverzeichnis & lineare/Halbjahres-AfA (§§ 7, 8, 13 EStG): `verified` (PR 13)
- Steuerberichte, TaxEvents & Vorsteuerermittlung: `verified` (PR 1, 6, 10)

### Profil `AT-EAR-KU` (Kleinunternehmer nach § 6 Abs. 1 Z 27 UStG)
- Schwellenwert-Überwachung (55.000 € / 10 % Toleranzregel gem. § 6 Abs. 1 Z 27 UStG): `verified` (PR 9)
- Steuerfreie Rechnungen mit gesetzlichem Steuerbefreiungshinweis: `verified` (PR 9)
- Reverse Charge- und Erwerbsteuer-Behandlung für Kleinunternehmer: `verified` (PR 9)
- Freiwillige Option zur Regelbesteuerung (§ 6 Abs. 3 UStG): `verified` (PR 9)

### Bedingte Module (serverseitig durch Capability-Gate technisch gesperrt)
- `AT-RKSV`: Registrierkassensicherheitsverordnung mit DEP & Signaturerstellung (`blocked` für AT-Mandanten mit HTTP 403 bis Zertifizierung/DEP, verifiziert in `test_at_conditional_modules.py`)
- `AT-ERB`: e-Rechnung.gv.at / ebInterface / Peppol BIS (`blocked` für AT-Mandanten mit HTTP 403 bis Golden-Files und Testeinbringung, verifiziert in `test_at_conditional_modules.py`)
- `AT-PAYROLL`: Österreichische Personalverrechnung (`blocked` für AT-Mandanten mit HTTP 403 bis ELDA/Finanzverwaltung-Schnittstellen, verifiziert in `test_at_conditional_modules.py`)

---

## 3. Historie der Verifikationen

| Datum | PR / Commit | Geprüfte Komponenten | Prüfergebnis |
|---|---|---|---|
| **2026-09-08** | PR 1 | `backend/services/number_parse.py`, `backend/routers/bank_imports.py`, `backend/routers/reports.py` | **26/26 Tests bestanden** (100 % grün auf `test_tax_reports.py`, `test_bank_imports.py`, `test_number_parse.py`, `test_tax_engine.py`) |
| **2026-09-08** | PR 2–9 | `backend/services/document_lifecycle.py`, `backend/services/document_snapshot.py`, `backend/services/account_roles.py`, `backend/services/at_tax_events.py`, `backend/localizations/at/*` | **24/24 Tests bestanden** (100 % grün auf Dokumentintegrität, Periodensperre, AT-Profil, Kontenrollen, AT-Rechnungsmerkmale, Steuersätze, TaxEvents, Reverse Charge, Kleinunternehmer) |
| **2026-09-08** | PR 10–15 | `backend/localizations/at/uva.py`, `backend/localizations/at/zm.py`, `backend/localizations/at/u1.py`, `backend/localizations/at/reconciliation.py`, `backend/localizations/at/ugb_reports.py`, `backend/localizations/at/ear.py`, `backend/localizations/at/depreciation.py`, `backend/localizations/at/goods_received.py`, `backend/localizations/at/archive.py`, `backend/localizations/at/income_tax_workpapers.py`, `backend/localizations/at/audit_export.py` | **17/17 Tests bestanden** (100 % grün auf UVA/U30, ZM, Steuerabstimmung, UGB-Bilanz/GuV, E/A-Rechnung & E1a, Halbjahres-AfA, Wareneingangsbuch, 7-Jahres-Aufbewahrung, KSt & MWR, Prüfexport-Paket) |
| **2026-09-08** | PR 16–18 | `backend/routers/pos.py`, `backend/routers/peppol.py`, `backend/routers/payroll.py`, `backend/localizations/at/profile.py` | **3/3 Tests bestanden** (100 % grün auf serverseitige Capability-Gates: POS/RKSV, Peppol/e-Rechnung, Payroll HTTP 403 Sperre) |
| **2026-09-09** | Korrekturlauf | Dokumentlebenszyklus, Profile, Capability-Gates, AfA, Meldungen, Migration und UI | **1.097/1.097 Backend-Tests und 51/51 AT-Tests bestanden; 3/3 BMF-XSDs validiert; Migration Up/Down/Up bestanden; UI-Audit 0 Befunde** |
