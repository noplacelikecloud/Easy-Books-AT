# Österreich-Compliance – Implementierungsplan

**Stand:** 8. September 2026  
**Ausgangsrevision:** `9501656a`  
**Aktueller Alembic-Head:** `0088_device_tokens`  
**Fachliche Grundlage:** [Österreich-Gap-Analyse](../../OESTERREICH_GAP_ANALYSE.md)  
**Ziel:** Easy-Books für österreichische KMU, insbesondere GmbH/FlexCo und Einzelunternehmen, innerhalb klar ausgewiesener Nutzungsprofile fachlich korrekt, nachvollziehbar und prüfbar betreibbar machen.

## 1. Zielzustand und verbindlicher Produktumfang

„Österreich-compliant“ wird nicht als einzelnes Boolean-Feld behandelt. Jeder AT-Mandant erhält ein versioniertes Compliance-Profil. Die Anwendung zeigt und erlaubt nur Geschäftsfälle, die für dieses Profil implementiert und freigegeben sind.

### 1.1 Freigabeprofile

| Profil | Enthaltener Nutzungsumfang | Freigabestatus am Ende dieses Plans |
| --- | --- | --- |
| `AT-UGB-VAT` | GmbH/FlexCo bzw. rechnungslegungspflichtiges Unternehmen, doppelte Buchführung, Soll- oder zulässige Istbesteuerung, AR/AP, Bank, Anlagen, österreichische Rechnungen, UVA-/ZM-Vorbereitung, UGB-Bilanz/GuV | verpflichtend |
| `AT-EAR-VAT` | Einzelunternehmen mit Einnahmen-Ausgaben-Rechnung, Soll-/Istbesteuerung, Anlagenverzeichnis, Wareneingangsbuch, E1a-Zuordnung, UVA-/ZM-Vorbereitung | verpflichtend |
| `AT-EAR-KU` | Einzelunternehmen mit E/A-Rechnung und Kleinunternehmerbefreiung einschließlich Grenzüberwachung; Sondersteuerschulden bleiben möglich | verpflichtend |
| `AT-RKSV` | Bargeschäfte über registrierkassenpflichtiges POS einschließlich RKSV und DEP | bedingtes Modul, vor Freigabe vollständig umsetzen oder für AT sperren |
| `AT-ERB` | Strukturierte Rechnung an den Bund über ebInterface/UBL und e-Rechnung.gv.at/Peppol | bedingtes Modul, vor Freigabe vollständig umsetzen oder für AT sperren |
| `AT-PAYROLL` | Österreichische Personalverrechnung einschließlich Lohnkonto und Schnittstellen zu ELDA/Finanzverwaltung | bedingtes Modul, vor Freigabe vollständig umsetzen oder für AT sperren |

Zum Pflichtumfang gehören normale inländische Umsätze, gemischte Steuersätze, Kleinunternehmer, Anzahlungen, Gutschriften/Entgeltminderungen, innergemeinschaftliche Lieferungen und Erwerbe, EU-B2B-Dienstleistungen, Reverse Charge, Ausfuhr sowie Standard-Fremdwährungsvorgänge. Branchen- und Sondersysteme wie Differenzbesteuerung, Reiseleistungen, Grundstücksumsätze, Land-/Forstwirtschaftspauschalierung, OSS/IOSS, Dreiecksgeschäfte und Organschaft erhalten eigene Capability-Flags. Solange die jeweilige Regel nicht umgesetzt und freigegeben ist, lehnt das Backend den Fall mit einer eindeutigen fachlichen Fehlermeldung ab.

### 1.2 Definition of Done für den Gesamtplan

Der Zielzustand gilt erst als erreicht, wenn:

1. alle P0- und P1-Befunde `AT-01` bis `AT-12` und `AT-15` geschlossen sind;
2. Profile `AT-UGB-VAT`, `AT-EAR-VAT` und `AT-EAR-KU` die Abnahmematrix dieses Plans vollständig bestehen;
3. bedingte Module entweder ihre eigene Abnahme bestehen oder bei AT-Mandanten serverseitig gesperrt sind;
4. jede steuerliche Zahl vom Bericht über `TaxEvent` bis zum festgeschriebenen Ursprungsbeleg und zur Hauptbuchbuchung nachvollziehbar ist;
5. Migration, Backup, Restore und vollständiger Prüfexport auf SQLite und PostgreSQL getestet sind;
6. ein österreichischer Bilanzbuchhalter/Steuerberater die fachlichen Testfälle, UVA-Kennzahlen und Beispielabschlüsse schriftlich abgenommen hat;
7. die Produktdokumentation den freigegebenen Umfang und die weiterhin gesperrten Sonderfälle exakt nennt.

## 2. Architekturentscheidungen vor dem ersten Feature-PR

Diese Entscheidungen verhindern, dass österreichische Regeln erneut über verstreute Kontonummern und UI-Bedingungen eingebaut werden.

### 2.1 Versioniertes Compliance-Profil

Neue Tabelle `AccountingProfileVersion`:

- `tenant_id`, `jurisdiction="AT"`, `valid_from`, `valid_to`
- `legal_form`: `sole_proprietor|gmbh|flexco|og|kg|other`
- `profit_method`: `ugb_double_entry|ear`
- `vat_status`: `standard|small_business_exempt|opted_in`
- `vat_method`: `accrual|cash`
- `vat_filing_frequency`: `monthly|quarterly|annual_only`
- `fiscal_year_start`, `tax_number`, `vat_id`
- `company_register_number`, `company_register_court`, `registered_seat`
- `capabilities` als validiertes JSON für ausdrücklich unterstützte Sonderfälle
- `created_at`, `created_by_id`, `change_reason`

Das Profil ist effective-dated. Änderungen erzeugen eine neue Version und überschreiben keine frühere Einordnung. Überschneidende Gültigkeiten sind verboten. `country="AT"` allein aktiviert keine Steuerlogik.

### 2.2 Semantische Kontenrollen

Neue Tabelle `AccountRoleBinding` mit eindeutigem `(tenant_id, role_key, valid_from)`-Mapping. Mindestens:

- `accounts_receivable`, `accounts_payable`, `cash`, `bank`
- `inventory`, `revenue`, `expense`, `retained_earnings`
- `vat_output`, `vat_input`, `vat_rc_output`, `vat_rc_input`
- `vat_non_deductible`, `customer_advances`, `vendor_advances`
- `fx_gain`, `fx_loss`, `rounding_difference`

Buchungsservices lösen Rollen auf; neue AT-Pfade verwenden keine fest codierten Kontonummern. Bestehende Settings werden einmalig in Rollen überführt. Der österreichische Kontenplan ist eine Vorlage mit UGB-Berichtszuordnung, keine unveränderbare gesetzliche Nummernliste.

### 2.3 Festschreibung statt Buchung bei Anlage

Rechnungen und Eingangsrechnungen werden künftig als echte Entwürfe angelegt. Erst `POST /api/invoices/{id}/finalize` bzw. `POST /api/bills/{id}/finalize` vergibt die endgültige Nummer, validiert das AT-Profil, erzeugt den unveränderlichen Snapshot, schreibt Hauptbuch und Steuerjournal und rendert die archivierte Ausgabe.

Statusdimensionen werden getrennt:

- `lifecycle_status`: `draft|finalized|corrected|cancelled`
- `delivery_status`: `not_sent|sent|accepted|rejected`
- `settlement_status`: `unpaid|partial|paid|overpaid`
- `approval_status`: vorhandener Workflow

Die bisherige einzelne Spalte `status` bleibt während der Migration als Kompatibilitätsfeld und wird erst entfernt, wenn alle Consumer umgestellt sind.

### 2.4 Vollständige Dokumentversion und Steuerjournal

Neue Tabelle `DocumentVersion`:

- Mandant, Dokumenttyp/-ID, fortlaufende Version, Zustand und Originalbezug
- vollständiger kanonischer JSON-Snapshot von Kopf, Parteien, Positionen, Steuerklassifikation, Konten und Währung
- SHA-256 des kanonischen Snapshots
- Pfade/Hashes der archivierten PDF-/XML-Ausgaben
- `recorded_at`, `recorded_by_id`, `effective_date`, `reason`

Neue Tabelle `TaxEvent`:

- Quelle und `document_version_id`
- `event_type`: `invoice|bill|payment|advance|credit|debit|write_off|adjustment|acquisition|import`
- ursprüngliches Ereignis für Korrekturen
- Leistungs-, Rechnungs-, Zahlungs-, Buchungs- und Steuerdatum
- Steuerperiode, Profilversion und Behandlungscode
- Bemessungsgrundlage/Steuer in Dokumentwährung und EUR, Kurs/Quelle
- Ausgangssteuer, Erwerb-/RC-Steuer, abziehbare und nicht abziehbare Vorsteuer
- UVA-/U1-/ZM-Kennzahlen, Partnerland und UID-Snapshot
- finaler Zustand und Audit-Metadaten

Steuerreports lesen ausschließlich `TaxEvent`. Das Hauptbuch bleibt Rechnungslegungsquelle; ein Abstimmreport vergleicht beide Ebenen.

### 2.5 Validierte Steuerbehandlung

`TaxCode` wird nicht nur um weitere Flags ergänzt. Eine neue effective-dated `TaxTreatmentVersion` speichert die gesamte Semantik:

- Jurisdiktion, Code und Richtung
- Art: `standard|reduced|zero_rated|exempt|outside_scope|reverse_charge|intra_eu_supply|intra_eu_acquisition|export|import_vat`
- Satz, Rechts-/Rechnungshinweis und Gültigkeit
- zulässige Dokumentrichtung, Waren-/Dienstleistungsart und Partnerregion
- UVA-/U1-/ZM-Mapping
- Eingangs-/Ausgangskontenrollen und standardmäßige Vorsteuerquote

Dokumentpositionen speichern den verwendeten Behandlungssnapshot. Fehlender, fremder, inaktiver oder zeitlich ungültiger Code führt im AT-Modus zu HTTP 422; kein Fallback auf Kopfsteuer oder aktuellen Satz.

### 2.6 Compliance-Feature-Gate

Zentrale Funktion `assert_capability(session, tenant_id, capability, on_date)` wird in jedem betroffenen Write-Pfad aufgerufen. Die UI blendet gesperrte Funktionen aus, aber das Backend ist die maßgebliche Grenze. `at_compliance` ist ein Localization-Modul mit Abhängigkeit `base`; `pos`, `hrm` und `eu_peppol` werden für AT nur gemeinsam mit ihren freigegebenen AT-Capabilities aktiv nutzbar.

## 3. Lieferfolge

Jeder Abschnitt entspricht einem reviewbaren PR. Abhängige PRs werden nacheinander gemergt. Gemeinsame P0-Korrekturen dürfen vor dem AT-Modul ausgerollt werden.

### PR 1 – Sicherheitsnetz, Compliance-Matrix und akute Rechenfehler

**Behebt:** AT-03, AT-09; schafft die Basis für alle weiteren Arbeiten.

**Ändern:**

- `backend/routers/reports.py`
- `backend/routers/bank_imports.py`
- `backend/services/money.py` oder neuer `backend/services/number_parse.py`
- `backend/tests/test_tax_reports.py`
- `backend/tests/test_bank_imports.py`
- `docs/OESTERREICH_COMPLIANCE_MATRIX.md`

**Aufgaben:**

- Steuerkonten aus TaxCode/AccountRoleBinding statt Namens-/Kontonummernheuristik bestimmen.
- Soll und Haben für Steuerkonten saldieren; stornierte Transaktionen und Korrekturen richtig berücksichtigen.
- Pakistanische Einkommensteuer aus allgemeinen Reports entfernen oder streng an das passende Länderprofil binden.
- Locale-bewussten Geldparser erstellen. CSV-Import verlangt ein Importprofil für Trennzeichen, Dezimalzeichen, Tausenderzeichen, Datum und Vorzeichenkonvention.
- Vor dem Speichern Vorschau mit Zeilenanzahl, Soll-/Habensummen, Fehlern und Datei-Hash ausgeben; Bestätigung verwendet genau diesen gehashten Parse-Stand.
- Regressionstest für `123,45`, `1.234,56`, `1,234.56`, negatives Vorzeichen, Leerzeichen, leere Werte und mehrdeutige Formate.
- Compliance-Matrix mit Capability, Status, gesetzlicher Grundlage, Owner, Tests und Freigabedatum anlegen.

**Done when:** Lagerbestandskonto erscheint nie als Vorsteuer; Korrekturen saldieren; mehrdeutige CSV-Werte werden abgelehnt und nicht still verändert.

### PR 2 – Unveränderliche Buchungsbelege und Zustandsmaschine

**Behebt:** AT-01, AT-02.

**Migration:** `0089_document_integrity.py`

**Ändern/neu:**

- `backend/models.py`: `DocumentVersion`, `DocumentNumberSeries`; Statusfelder und Unique Constraints
- `backend/services/document_lifecycle.py`
- `backend/services/document_snapshot.py`
- `backend/routers/invoices.py`, `bills.py`, `credit_notes.py`, `debit_notes.py`, `transactions.py`
- Frontend-Formulare und Detailseiten für Entwurf/Festschreibung/Storno
- `backend/tests/test_document_integrity_at.py`
- bestehende Edit-/Posting-/Approval-Tests migrieren

**Aufgaben:**

- Finalisierung als einzige Stelle für endgültige Nummer, Snapshot und Buchung einführen.
- Datenbank-Eindeutigkeit mindestens für `(tenant_id, number)` bei Invoice/Bill/CreditNote/DebitNote; Serienname im Snapshot festhalten.
- `DocumentNumberSeries` verwendet das fachliche Beleg-/Leistungsjahr gemäß definierter Serienregel und nicht unbemerkt das Systemdatum.
- Finalisierte Belege sind schreibgeschützt. Korrektur erzeugt ein neues Korrekturdokument und spiegelbildliche Buchung mit Originalbezug; ein Versandstatus ändert keine Buchung.
- Delete ist nur bei nie festgeschriebenen Entwürfen ohne `transaction_id`, Zahlung, Lagerbewegung oder abhängige Datensätze erlaubt.
- Bulk-Aktionen rufen dieselbe Zustandsmaschine wie Einzelaktionen auf; keine direkte Statusmutation.
- Bestehende gebuchte Datensätze bei Migration auf `finalized` setzen und einen als „legacy/reconstructed“ gekennzeichneten Snapshot aus den noch vorhandenen Daten erzeugen. Fehlende frühere Positionen nicht erfinden.
- Audit-Log protokolliert Grund, Benutzer, Zeitpunkt, Original-/Korrektur-ID und Hash.

**Done when:** Der Angriff „gebucht → draft → delete“ scheitert serverseitig; kein finalisierter Kopf oder keine finalisierte Position wird aktualisiert/gelöscht; eine Korrektur ist Ende-zu-Ende nachvollziehbar.

### PR 3 – Periodensperre, Abschlussintegrität und Audit

**Behebt:** AT-08 und den in der Analyse festgestellten Abschlussfehler.

**Migration:** `0090_period_close_control.py`

**Ändern/neu:**

- `backend/models.py`: Periodenzustand, Close-/Reopen-Historie, Snapshot-Hash
- `backend/routers/periods.py`
- `backend/services/close_pack.py`
- `backend/tests/test_at_period_control.py`

**Aufgaben:**

- Status `open|closing|closed|reopened` statt frei schaltbarem Boolean einführen.
- `toggle_period_lock` entfernen bzw. intern auf den kontrollierten Close-/Reopen-Service führen.
- Reopen nur für Owner oder eigenes Recht, mit Pflichtbegründung und Vier-Augen-Option; Abschlussstände bleiben versioniert.
- Perioden mit Buchungen, TaxEvents, Meldungen oder Dokumentversionen nie löschen.
- Jahresabschlussbuchung erzeugen, wenn P&L-Konten Salden besitzen, auch wenn das Nettoergebnis null ist; positive und negative Kontensalden spiegelbildlich schließen.
- Doppelte Abschlussbuchung nach Reopen verhindern bzw. alte Abschlussbuchung kontrolliert stornieren.
- Audit-Paket erhält Manifest mit Dateihashes, Profilversion, verwendeten Konten-/Berichtsmappings und Erstellungszeitpunkt.

**Done when:** Lock/Close/Reopen/Delete besitzen genau einen auditierten Pfad; Nullgewinn, Verlust und Gegenkontensalden bestehen die Tests ohne doppelte Ergebnisumbuchung.

### PR 4 – AT-Modul, Onboarding und semantischer Kontenplan

**Behebt:** Grundlage für AT-05, AT-11, AT-15.

**Migration:** `0091_at_profile_and_account_roles.py`

**Ändern/neu:**

- `backend/models.py`: `AccountingProfileVersion`, `AccountRoleBinding`, `ReportLineMapping`
- `backend/localizations/at/profile.py`
- `backend/localizations/at/coa.py`
- `backend/services/account_roles.py`
- `backend/routers/at_settings.py`
- `backend/db.py`: `at_compliance` in `MODULE_REGISTRY`
- Settings-/Onboarding-UI
- `backend/tests/test_at_profile.py`, `test_at_account_roles.py`

**Aufgaben:**

- Onboarding für Rechtsform, Gewinnermittlung, USt-Status/-Methode, Wirtschaftsjahr, Vorjahresumsatz, UID/Steuernummer und Capabilities.
- Zulässige Kombinationen serverseitig validieren; zeitliche Profiländerung statt Überschreiben.
- EUR und `Europe/Vienna` für neue AT-Mandanten; Basiswährungsänderung nach erster Buchung sperren.
- AT-Kontenplanvorlage mit Kontenrollen und UGB-/E1a-Berichtsmapping bereitstellen. Existierende Mandanten werden durch einen expliziten Mapping-Assistenten migriert, nicht durch stilles Reseeding.
- Alle neuen AT-Buchungen lösen Kontenrollen auf. Eine Inventur bestehender hart codierter Kontenstellen wird als Checkliste im PR geführt; AT-relevante Pfade werden umgestellt.
- Frontend ergänzt `de-AT`; Zahlen, Geld und Datum verwenden gemeinsame formatierte Helfer. `app_language` erlaubt `de`.
- Capability-Gate einführen und POS/Payroll/Public-eInvoice für AT zunächst sperren.

**Done when:** Ein frischer Mandant kann jedes der drei Pflichtprofile wählen; daraus entstehen konsistente Einstellungen und Rollen; nach erster Buchung ist Basiswährungsänderung gesperrt; keine AT-Buchung hängt von `1200`/`2200`/`3100` ab.

### PR 5 – Parteien, österreichische Rechnungsfelder und PDF

**Behebt:** AT-06 und Teile von AT-05.

**Migration:** `0092_at_party_and_invoice_fields.py`

**Ändern/neu:**

- `backend/models.py`: strukturierte Adressen/AT-IDs bzw. neue `PartyAddress`/`PartyTaxIdentity`
- Invoice/Bill und Lines: Leistungsdatum/-zeitraum, Steuerbehandlungssnapshot
- `backend/localizations/at/invoice_validation.py`
- `backend/templates/invoice_at.html`, `credit_note_at.html`
- `backend/services/pdf.py`, `print_templates.py`
- Invoice-/Customer-/Vendor-Frontend
- `backend/tests/test_at_invoice_requirements.py`

**Aufgaben:**

- Firmenname, Rechtsform, Sitz, Firmenbuchnummer/-gericht, Steuernummer und UID getrennt erfassen; strukturierte Partneranschrift, Land, Unternehmereigenschaft und UID.
- UID-Prüfung mit Ergebnis, Zeitpunkt, Abfragemethode und Name/Adresse speichern; technische Ausfälle von negativer Validierung unterscheiden.
- Pflichtfeldmatrix nach Inland/EU/Drittland, B2B/B2C, Betrag und Tatbestand.
- Grenzwerte exakt testen: 400,00/400,01 und 10.000,00/10.000,01 Euro brutto.
- Leistungsdatum/-zeitraum wird steuerlich maßgeblich, soweit der Tatbestand es verlangt.
- PDF gruppiert Netto und Steuer je Behandlung/Satz und zeigt gesetzlich erforderliche Hinweise. Der Template-Editor kann Pflichtdaten nicht aus AT-finalisierten Ausgaben entfernen; Compliance-Footer/-Block wird außerhalb des frei änderbaren Templates gerendert.
- Bei Finalisierung die tatsächlich ausgegebene PDF und den vollständigen Snapshot archivieren.

**Done when:** Normale AT-Rechnungen und Gutschriften bestehen die Pflichtfeldmatrix; Mischsteuersätze stimmen in UI, PDF und Snapshot überein; spätere Stammdatenänderungen verändern alte Ausgaben nicht.

### PR 6 – Steuerbehandlungen 20/13/10/4,9/0 und historische Regeln

**Behebt:** AT-05 und schafft die Grundlage für AT-04/AT-10.

**Migration:** `0093_tax_treatments.py`

**Ändern/neu:**

- `backend/models.py`: `TaxTreatmentVersion`, zusätzliche Positionssnapshots
- `backend/localizations/at/tax_catalog.py`
- `backend/services/tax_engine.py`
- `backend/routers/tax_codes.py`
- Produktklassifikation mit KN-/Sachmerkmalen, soweit für 4,9 % benötigt
- `backend/tests/test_at_tax_treatments.py`

**Aufgaben:**

- AT-Katalog für 20 %, 13 %, 10 %, 4,9 %, Nullsatz, Befreiungen, Nichtsteuerbarkeit und Sondertatbestände.
- 4,9 % ab 01.07.2026 nur für freigegebene Anlage-3-Klassifikationen; kein pauschales Lebensmittel-Flag. Gastronomie-/kombinierte Leistungen werden getrennt behandelt.
- Volle Semantik effective-dated versionieren; keine historische Umklassifizierung über heutige TaxCode-Flags.
- Fehlende Gültigkeitsintervalle und Richtungsfehler hart ablehnen.
- Übergangsfälle für Anzahlungen, Leistung und Retouren am 30.06./01.07.2026 testen.
- Rundungspolitik pro Position und Steuergruppe definieren; Differenzbuchung transparent auf die dafür gebundene Rolle.

**Done when:** alle Sätze werden korrekt gerechnet, gebucht und gruppiert; alte Dokumente bleiben nach Katalogänderung unverändert; Übergangsfälle bestehen.

### PR 7 – Steuerereignis-Engine, Soll/Ist, Anzahlungen und Korrekturen

**Behebt:** Kern von AT-04, AT-05 und AT-10.

**Migration:** `0094_tax_events.py`

**Ändern/neu:**

- `backend/models.py`: `TaxEvent`, `TaxPeriod`, `TaxAdjustment`
- `backend/services/at_tax_events.py`
- `backend/services/posting.py` für atomare Buchung + Events
- `backend/routers/invoices.py`, `bills.py`, `payments.py`, `advances.py`, `credit_notes.py`, `debit_notes.py`
- `backend/tests/test_at_tax_events.py`

**Aufgaben:**

- Steuerdatum regelbasiert aus Profil, Tatbestand, Leistung, Rechnung und Zahlung ermitteln.
- Sollbesteuerung einschließlich möglicher Einmonatsverschiebung; Istbesteuerung je tatsächlichem Zahlungseingang und anteiliger Steuergruppe.
- Anzahlungs-/Teilzahlungsereignisse und Schlussrechnung mit Anrechnungsbezug umsetzen.
- Vorsteuerzeitpunkt, Zahlungsbedingung für einschlägige Istbesteuerer und Abzugsquote modellieren.
- Entgeltminderung, Skonto, Retoure, Uneinbringlichkeit und Korrektur referenzieren das ursprüngliche Event und dessen Satz.
- Erfassungs-/Wirksamkeitsdatum unterscheiden; geschlossene Periode führt zu Korrektur in zulässiger Periode mit Originalbezug, nicht zu unkontrollierter Rückdatierung.
- Eventerzeugung und GL-Posting in einer DB-Transaktion. Ein idempotency key verhindert doppelte Events bei Retries.

**Done when:** Soll/Ist, Teilzahlung, Anzahlung, Schlussrechnung und Korrektur sind ohne doppelte oder fehlende Steuer anhand einer Ereigniskette erklärbar.

### PR 8 – Reverse Charge, innergemeinschaftlicher Erwerb und EU/Drittland

**Behebt:** AT-04 vollständig.

**Ändern/neu:**

- `backend/localizations/at/cross_border.py`
- `backend/services/tax_engine.py`, `at_tax_events.py`, `posting.py`
- Invoice-/Bill-Formulare für Leistungsart, Partnerland, UID und Nachweise
- `backend/tests/test_at_cross_border_tax.py`

**Aufgaben:**

- Eigene Regeln für EU-B2B-Dienstleistung, innergemeinschaftliche Lieferung, innergemeinschaftlichen Erwerb, inländisches Reverse Charge, Ausfuhr und Einfuhrumsatzsteuer.
- Eingangs-RC bucht Steuerschuld und abzugsfähige/nicht abzugsfähige Vorsteuer getrennt; Rechnungsverbindlichkeit bleibt netto.
- Volle, teilweise und keine Vorsteuerberechtigung testen.
- Steuerfreie innergemeinschaftliche Lieferung nur mit den erforderlichen UID-/Nachweismerkmalen; fehlende Nachweise blockieren Finalisierung oder führen in einen ausdrücklich vorgesehenen Review-Status.
- Automatische Peppol-Regel „Buyer-ID + 0 % = RC“ entfernen; XML übernimmt Behandlungssnapshot.
- ZM-Relevanz aus Tatbestand bestimmen, nicht allein aus UID/Land.

**Done when:** 100 Euro EU-Leistungsbezug erzeugt bei 20 % genau 100 Euro Verbindlichkeit, 20 Euro Steuerschuld und die zulässige Vorsteuer; Export-/EU-Nachweise sind am Event verknüpft.

### PR 9 – Kleinunternehmerstatus und Grenzüberwachung

**Behebt:** Pflichtprofil `AT-EAR-KU`.

**Migration:** `0095_at_small_business.py`

**Ändern/neu:**

- `backend/models.py`: `SmallBusinessThresholdLedger` oder ableitbare, versionierte Umsatzklassifikation
- `backend/localizations/at/small_business.py`
- Dashboard-/Settings-Warnungen
- `backend/tests/test_at_small_business.py`

**Aufgaben:**

- Maßgebliche Umsätze im laufenden und vorangegangenen Kalenderjahr nach gesetzlichen Ein-/Ausschlüssen ermitteln.
- Grenze 55.000 Euro und 10-%-Überschreitungsregel transaktionsgenau anwenden.
- Statuswechsel ab überschreitendem Umsatz bzw. Folgejahr effective-dated planen; Belege vor dem Wechsel bleiben unverändert.
- Verzicht/Option samt Gültigkeit und dokumentierter Entscheidung speichern.
- Keine Umsatzsteuer auf regulären KU-Rechnungen; Pflicht-Hinweis aus Behandlung. RC-/Erwerbs- oder andere Sondersteuerschuld wird nicht pauschal deaktiviert.

**Done when:** Grenztests 55.000, 60.500 und darüber einschließlich Einzelumsatz und Vorjahr bestehen; die App kann erklären, welcher Umsatz den Status wann geändert hat.

### PR 10 – UVA, U1, ZM und FinanzOnline-Dateiexport

**Behebt:** AT-10.

**Migration:** `0096_at_tax_filings.py`

**Ändern/neu:**

- `backend/models.py`: `TaxFiling`, `TaxFilingVersion`, `TaxFilingSubmissionLog`
- `backend/localizations/at/uva.py`, `u1.py`, `zm.py`
- `backend/routers/at_tax.py`
- Frontend `/at/tax`
- offizielle XSDs/Versionsmetadaten als kontrollierte Referenz oder Build-Download mit Hash
- `backend/tests/test_at_uva.py`, `test_at_zm.py`, `test_at_tax_reconciliation.py`

**Aufgaben:**

- Kennzahlenauswertung ausschließlich aus finalisierten TaxEvents; Dokumentstatus, Gutschriften, Zahlungen und Währungsumrechnung berücksichtigen.
- UVA-Version nach Meldezeitraum; ab 07/2026 bzw. Q3/2026 KZ 124/125.
- monatliche/vierteljährliche Perioden und Fälligkeit aus Profil und Vorjahresumsatz vorschlagen; Benutzer kann nur mit dokumentierter Grundlage abweichen.
- Filing-Snapshot mit enthaltenen Event-IDs/Hashes; nach Finalisierung unveränderlich. Korrekturmeldung als neue Version/Differenz.
- XML gemäß offizieller FinanzOnline-Struktur erzeugen und lokal gegen XSD plus fachliche Regeln validieren. Zunächst Download; direkte Übermittlung erst in eigenem, abgenommenem PR.
- ZM nach Partner-UID/Tatbestand/Periode; Frist und Summenprüfung.
- Abstimmung: TaxEvent-Summen ↔ UVA-Kennzahlen ↔ Steuerkonten im Hauptbuch. Differenzen blockieren Finalisierung.
- U1-Jahresauswertung als Vorbereitung; keine Behauptung automatischer Einreichung ohne Übermittlungsbestätigung.

**Done when:** amtliche Beispiel-/Golden-Files validieren; Vor-/Nach-Juli-2026-Fälle stimmen; jede Kennzahl ist bis zu Belegversion und GL erklärbar.

### PR 11 – UGB-Bilanz, GuV und Abschlussworkflow

**Behebt:** AT-11 für doppelte Buchführung.

**Migration:** `0097_at_financial_statements.py`

**Ändern/neu:**

- `backend/localizations/at/ugb_reports.py`
- `backend/services/account_tree.py`
- `backend/routers/reports.py` oder eigener `at_reports.py`
- Abschluss-UI und Mapping-Assistent
- `backend/tests/test_at_ugb_statements.py`

**Aufgaben:**

- Bilanzgliederung nach § 224 UGB und GuV nach § 231 UGB als versioniertes Report-Schema.
- Konten-/Rollup-Mapping mit Validierung, dass alle formellen Konten genau einer zulässigen Position zugeordnet sind; Memo-/Hilfskonten separat.
- Vorjahresvergleich, leere/zusammenfassbare Positionen, Größenklasse und Gewinn-/Verlustvortrag.
- Abschlusscheckliste für Saldenabstimmung, Debitoren/Kreditoren, Bank, Inventur, Anlagevermögen, Steuern, Abgrenzungen, Rückstellungen und Ereignisse nach Stichtag.
- IFRS-only-Automatik in AT-UGB-Berichten und -Buchungspfaden sperren oder als eindeutig getrennte Nebenrechnung führen.
- Berichtsversion und verwendete Mappings im Audit-Paket speichern.

**Done when:** Golden-Mandanten für Gewinn, Verlust, Nullergebnis, negatives Eigenkapital und Vorjahresvergleich erzeugen gesetzeskonform gegliederte, abgestimmte Berichte.

### PR 12 – Einnahmen-Ausgaben-Rechnung, Anlagenverzeichnis und Wareneingangsbuch

**Behebt:** AT-11 für Einzelunternehmen.

**Migration:** `0098_at_ear.py`

**Ändern/neu:**

- `backend/localizations/at/ear.py`
- `backend/models.py`: steuerliche Klassifikation für Zahlungsanteile/Privatanteile
- `backend/routers/at_ear.py`
- Frontend `/at/ear`
- `backend/tests/test_at_ear.py`, `test_at_goods_received_book.py`

**Aufgaben:**

- E/A-Bericht nach Zufluss/Abfluss aus Zahlungen und gesetzlich abweichenden Ereignissen; keine bloße Filterung der GuV.
- Einlagen, Entnahmen, Privatanteile, nicht abzugsfähige Ausgaben und AfA getrennt.
- E1a-/E1a-K-Mapping versionieren und als Arbeitsunterlage exportieren.
- Wareneingangsbuch chronologisch mit fortlaufender Eintragung, Lieferant/Anschrift, Bezeichnung, Einzelpreis brutto/netto und Belegbezug; Monats-/Jahressummen.
- Anlagenverzeichnis mit Lieferant, Anschaffung/Inbetriebnahme, Kosten, Nutzungsdauer, Jahres-AfA und Restwert.
- Wechsel `ear → ugb_double_entry` als eigener Migrationsworkflow mit Eröffnungsbilanz und offenen Steuerereignissen.

**Done when:** Ein Beispiel-Einzelunternehmen liefert für Teilzahlungen, unbezahlte Rechnungen, Anlagen, Privatanteile und Warenbezug eine nachvollziehbare E/A und vollständige Nebenverzeichnisse.

### PR 13 – Österreichische Anlagen-Nebenrechnung

**Behebt:** AT-12.

**Migration:** `0099_at_asset_valuation.py`

**Ändern/neu:**

- `backend/models.py`: getrennte Book-/Tax-Basis und Bewegungen
- `backend/localizations/at/depreciation.py`
- `backend/services/assets.py`, `depreciation.py`
- Anlagen-Frontend und Rollforward
- `backend/tests/test_at_depreciation.py`

**Aufgaben:**

- UGB- und Steuerwerte getrennt führen; jede Bewegung besitzt Grundlage und Gültigkeitsjahr.
- Inbetriebnahmedatum und Halbjahresregel, lineare und zulässige degressive AfA, GWG bis 1.000 Euro sowie Wechsel der Methode.
- Vorsteuerabzugsquote in Anschaffungskosten einbeziehen.
- Kategorien/Sonderregeln für Gebäude, Pkw/Kombi, emissionsfreie Fahrzeuge, Firmenwert und ausgeschlossene degressive Güter.
- Abgang, Teilabgang, Zuschreibung, außerplanmäßige Abschreibung und Vorsteuerberichtigung mit Auditbezug.

**Done when:** Golden-Fälle für erstes/zweites Halbjahr, GWG, teilweisen Vorsteuerabzug, Gebäude/Pkw und Abgang stimmen in UGB-, Steuer- und E/A-Sicht.

### PR 14 – Archiv, Aufbewahrung, Legal Hold und vollständiger Export

**Behebt:** AT-07.

**Migration:** `0100_retention_archive.py`

**Ändern/neu:**

- `backend/models.py`: `RetentionRecord`, `ArchiveObject`, `LegalHold`
- `backend/services/archive.py`, `retention.py`
- `backend/routers/attachments.py`, `backup.py`
- Admin-UI für Export/Restore/Legal Hold
- `backend/tests/test_at_retention.py`, `test_full_backup_restore.py`

**Aufgaben:**

- SHA-256, MIME, Größe, Speicherort, Version, Aufbewahrungskategorie und `retain_until` für Originale und Ausgaben.
- Löschung während Frist, Verfahren oder Legal Hold serverseitig verhindern. Nach Frist kontrollierter Löschlauf mit Protokoll.
- Anhänge finalisierter Belege nicht ersetzen; Ergänzungen als neue Archivobjekte.
- Vollständiger Tenant-Export: DB-Datensätze, Audit, Dokumentversionen, TaxEvents, Meldungen, PDF/XML und externe Supabase-Objekte mit Manifest/Hashes.
- Restore-Test stellt einen leeren Zielmandanten bzw. eine isolierte Testinstanz wieder her und prüft Hashes/Beziehungen.
- PostgreSQL-Betrieb erhält dokumentierte Backup-/PITR-Anforderungen; SQLite-Backup trennt Platform-Owner- von Tenant-Admin-Rechten.

**Done when:** vollständiger Export und Restore bestehen; eine vorzeitig gelöschte Belegdatei ist über API und direkten App-Pfad ausgeschlossen bzw. als Integritätsalarm sichtbar.

### PR 15 – AT-Ertragsteuer-Arbeitsunterlagen und Kanzleiexport

**Behebt:** Rest von AT-10; unterstützt die betriebliche Übergabe.

**Ändern/neu:**

- `backend/localizations/at/income_tax_workpapers.py`
- `backend/routers/at_tax.py`
- `backend/services/exports/at_bookings.py`
- `backend/tests/test_at_income_tax_workpapers.py`, `test_at_accountant_export.py`

**Aufgaben:**

- Pakistanische Tariflogik im AT-Kontext vollständig ausschließen.
- KSt-Arbeitsunterlage mit jahresbezogenem Satz (2026 grundsätzlich 23 %) und steuerlicher Mehr-/Weniger-Rechnung; Bilanzgewinn nicht als steuerliche Bemessungsgrundlage ausgeben.
- Einzelunternehmer: betriebliches Ergebnis/E1a-Daten liefern; persönliche Einkommensteuer nur als klar versionierte, vollständig getestete Zusatzfunktion.
- Generischer Kanzleiexport mit dokumentiertem Schema: Buchungs-/Belegdatum, Nummer, Konto/Gegenkonto, Betrag/Währung/EUR, Steuerschlüssel, Partnerkonto, Text und Archivbezug.
- BMD/RZL-spezifische Adapter erst nach bestätigter Zielversion und Golden-File der empfangenden Kanzlei benennen/freigeben.

**Done when:** kein AT-Bericht enthält ITO- oder 29-%-Defaults; Export ist round-trip-testbar und mit einer Pilotkanzlei abgestimmt.

## 4. Bedingte Module

Diese Arbeit gehört zum Gesamtziel. Sie darf parallel nach stabiler Dokument-/Steuerengine beginnen, bleibt aber für AT bis zur eigenen Abnahme gesperrt.

### PR 16 – RKSV / Registrierkasse

**Abhängigkeit:** PR 2, 4, 6, 7 und 14.

- Architekturentscheidung: zertifizierungs-/signaturfähiger eigener RKSV-Adapter oder geprüfte externe Kassenintegration.
- Pro Kasse DEP, Verkettung, Signatur-/Siegelerstellung, Belegmerkmale, Start-/Monats-/Jahres-/Schlussbelege, Ausfall/Wiederinbetriebnahme, Trainings-/Stornobelege und FinanzOnline-Prozesse.
- 4,9-%-Satz und aktuelle BMF-Detailvorgaben berücksichtigen.
- Digitale Belegbereitstellung ab 01.10.2026 plus Recht auf Papierbeleg.
- Export und Prüfung mit BMF-Prüftool/QR-Validierung; Manipulations-, Uhrzeit-, Offline- und Wiederherstellungstests.

**Done when:** externe technische Prüfung und fachliche Pilotabnahme bestanden; erst dann `AT-RKSV` Capability aktivieren.

### PR 17 – e-Rechnung.gv.at / Peppol

**Abhängigkeit:** PR 5, 6, 8 und 14.

- UBL 2.1/Peppol BIS sowie mindestens ein unterstütztes ebInterface-Format aus demselben Dokument-/Steuersnapshot erzeugen.
- Bundesspezifische Auftragsreferenz, Lieferantennummer und Empfängerregeln.
- Offizielle Schema- und Geschäftsregelvalidatoren; Test-/Produktionskanal getrennt.
- Submission-Log speichert Requesthash, Empfangs-/Fehlerantwort, Zeit, Retry und finalen Status.
- Versand gilt erst mit positiver Gegenstellenantwort als angenommen.

**Done when:** Golden-Files der öffentlichen Verwaltung validieren und Testeinbringung akzeptiert wird; dann `AT-ERB` aktivieren.

### PR 18 – Österreichische Personalverrechnung oder geprüfte Übergabe

**Abhängigkeit:** PR 4 und 14.

Zunächst entscheiden:

1. vollständige AT-Lohnengine mit jahres-/KV-abhängigen Regeln, Lohnkonto, Lohnsteuer, SV, Sonderzahlungen, DB/DZ/Kommunalsteuer sowie ELDA-/Finanz-Schnittstellen; oder
2. HR-Stammdaten und Import geprüfter Lohnbuchungsbelege aus einem externen Lohnsystem.

Variante 2 ist für die erste produktive Buchhaltung empfohlen. Das bestehende Payroll-Modul wird bei AT-Mandanten als „nicht zur österreichischen Lohnabrechnung freigegeben“ gesperrt, bis Variante 1 alle Golden-Files und Schnittstellentests besteht.

**Done when:** gewählte Produktgrenze technisch erzwungen ist; `AT-PAYROLL` nur nach eigener fachlicher/technischer Abnahme.

## 5. Querschnittstests und Prüfpyramide

### 5.1 Pro PR

- Pure-Logic-Tests für Steuerdatum, Sätze, Rundung, Grenzwerte und Berichtszuordnung.
- API-Integrationstests mit Mandant A/B für jede neue Ressource.
- DB-Invarianten und Migrationstest auf SQLite und PostgreSQL.
- Atomaritätstest: simuliertes Scheitern zwischen GL, TaxEvent, Snapshot und Archiv hinterlässt nichts Halbfinales.
- Idempotenztest für Finalisierung, Meldung und externe Übertragung.

### 5.2 Golden-Dataset

Neues, kleines und deterministisches `backend/tests/fixtures/at_golden/`:

- GmbH mit Sollbesteuerung, gemischten Steuersätzen, EU-Einkauf, Anlage und Jahresabschluss.
- Einzelunternehmen mit E/A und Istbesteuerung, Teilzahlungen, Warenbuch und AfA.
- Kleinunternehmer mit Grenzüberschreitung und RC-Leistungsbezug.
- Optionaler Handelsmandant mit RKSV sowie Bundeskunde nach Aktivierung der Module.

Jeder Beleg hat erwartete GL-Zeilen, TaxEvents, UVA-/ZM-Kennzahlen, PDF-Steuergruppen und Abschluss-/E/A-Zeilen. Erwartungsdateien werden fachlich geprüft und versioniert; Tests dürfen die Erwartung nicht aus derselben Produktionsfunktion erzeugen.

### 5.3 End-to-End-Abnahmefälle

Die 15 Fälle aus der Gap-Analyse sind Mindestumfang. Ergänzend:

- gleichzeitige Finalisierung zweier Dokumente derselben Serie;
- API-Retry nach Timeout ohne doppelte Nummer/Buchung/Steuer;
- Profilwechsel Ist → Soll und KU → Regelbesteuerung mit offenen Posten;
- Stichtag in Sommer-/Winterzeit und Server in anderer Zeitzone;
- Steuercodeänderung nach Abschluss/Meldung ohne Veränderung der Historie;
- Ausfall des UID-Dienstes, Archivs bzw. externen Einreichungskanals;
- Wiederherstellung aus Backup und erneute Abstimmung aller Hashes.

### 5.4 Standardbefehle

Nach jedem Backend-PR:

```bash
cd backend
uv run alembic upgrade head
uv run pytest tests/test_at_*.py -v
uv run pytest
```

Für neue Migrationen zusätzlich PostgreSQL über `PYTEST_POSTGRES=1` und eine isolierte `TEST_DATABASE_URL`. Nach Frontend-Änderungen gemäß `frontend/AGENTS.md` zuerst relevante Next.js-16-Dokumentation aus `node_modules/next/dist/docs/` lesen, danach:

```bash
cd frontend
npm run lint
npm test
npm run build
npm run test:e2e
```

E2E muss mindestens Onboarding, Rechnung finalisieren/korrigieren, Zahlung, UVA-Abstimmung, Abschluss und E/A-Bericht abdecken.

## 6. Migration bestehender Mandanten

Keine bestehende Firma wird automatisch als AT-konform markiert.

1. Preflight-Bericht ermittelt Land/Währung, festgeschriebene/gebuchte Entwürfe, Nummernduplikate, fehlende Positionen, Steuer-Fallbacks, historische Änderungen, harte Kontenabhängigkeiten, externe Anhänge und verdächtige Bankimporte.
2. Mandant wählt Profil und Stichtag. Vor Stichtag bleiben Datensätze `legacy`; ab Stichtag gelten harte AT-Regeln.
3. Kontenrollen und Reportzeilen werden durch Benutzer/Kanzlei gemappt und saldenmäßig geprüft.
4. Eröffnungssalden, offene Posten, Anlagen, Anzahlungen und Steuerpositionen werden abgestimmt.
5. Vorhandene Dokumente erhalten rekonstruierte Legacy-Snapshots mit Qualitätsstatus. Nicht vorhandene Originaldaten werden als Lücke ausgewiesen.
6. Vollbackup und Exportmanifest vor Aktivierung; Aktivierung selbst wird auditiert.
7. Nach Aktivierung wird ein Parallelvergleich für mindestens eine Meldeperiode empfohlen: bisherige Kanzleiberechnung gegen App-UVA/E/A/UGB-Berichte.

Rollback nach Aktivierung darf keine finalisierten Datensätze löschen. Das Profil wird mit neuem Gültigkeitszeitraum deaktiviert; Buchungen und Steuerereignisse bleiben erhalten und exportierbar.

## 7. Fachliche Freigabe und Release-Gates

### Gate A – Engineering

- alle relevanten Tests grün auf SQLite/PostgreSQL;
- keine ungeprüften TaxCode-Fallbacks, direkten Statusmutationen oder harten AT-Kontonummern;
- Tenant-Isolation und Berechtigungen geprüft;
- Migrations- und Restore-Test bestanden.

### Gate B – Fachliche Abnahme

- österreichische Steuerberatung/Bilanzbuchhaltung prüft Golden-Dataset, Belegbilder, Buchungssätze, UVA/ZM, E/A und UGB-Abschluss;
- Abweichungen werden als Test und Regeländerung dokumentiert;
- Rechts-/Formularversion und Prüfer/Freigabedatum stehen in der Compliance-Matrix.

### Gate C – Pilotbetrieb

- je ein Pilot für `AT-UGB-VAT`, `AT-EAR-VAT`, `AT-EAR-KU`;
- Parallelrechnung einer vollständigen UVA-Periode und eines Abschlusses bzw. E/A-Jahres;
- Export wird von Pilotkanzlei eingelesen und abgestimmt;
- Restore und Prüfexport werden praktisch durchgeführt.

### Gate D – Produktfreigabe

- Marketing, Onboarding und Hilfe nennen den tatsächlich freigegebenen Umfang;
- bedingte/unfertige Sonderfälle sind technisch gesperrt;
- Aktualisierungsprozess für Gesetze, BMF-Formulare, XSDs und Steuersätze besitzt Owner, Stichtag, Regressionstests und Release-Notiz;
- keine pauschale Aussage „vollständig rechtskonform“ ohne Profil-/Versionsbezug.

## 8. Empfohlene Meilensteine

| Meilenstein | Enthält | Nutzbarer Zustand |
| --- | --- | --- |
| M1 – Integritätskern | PR 1–3 | sichere Basis; noch keine AT-Freigabe |
| M2 – AT-Rechnung | PR 4–6 | AT-Stammdaten und korrekte Rechnungsdarstellung; noch keine UVA-Freigabe |
| M3 – AT-Umsatzsteuer | PR 7–10 | VAT-/KU-Profile einschließlich UVA/ZM-Vorbereitung freigabefähig |
| M4 – Jahres-/E/A-Abschluss | PR 11–15 | drei Pflichtprofile vollständig pilotfähig |
| M5 – Bedingte Module | PR 16–18 | RKSV, Bundese-Rechnung, Payroll jeweils separat freigabefähig |

Der kritische Pfad ist PR 1 → 2 → 4 → 5 → 6 → 7 → 8 → 10 → 11/12 → 13/14 → 15. PR 3 kann nach PR 2 parallel zu PR 4 vorbereitet werden. Bedingte Module beginnen erst nach stabiler Dokument-, Steuer- und Archivarchitektur.

## 9. Erstes ausführbares Arbeitspaket

Als nächster Implementierungsschritt wird **PR 1** umgesetzt. Er verändert noch kein Steuerprofil und hat geringe Migrationsgefahr, beseitigt aber zwei bestätigte Daten-/Berichtsfehler. Reihenfolge:

1. failing Regressionstests für Lagerkonto im Steuerbericht und europäische/US-Zahlenformate;
2. gemeinsamer, explizit konfigurierter Geldparser samt Vorschauvertrag;
3. Tax-Report auf tatsächliche Steuercodes und Nettobewegungen umstellen;
4. pakistanische Schätzung aus dem generischen Endpoint herauslösen;
5. Backend-Gesamttests und gezielte Frontend-Vertragstests;
6. Compliance-Matrix mit Status `not_started|in_progress|verified|blocked` anlegen.

Nach PR 1 beginnt die Belegintegrität in PR 2. Eine AT-Freigabe erfolgt erst mit M4 und den Gates A bis D; einzelne optionale Capabilities erst nach M5 und ihrer jeweiligen Abnahme.
