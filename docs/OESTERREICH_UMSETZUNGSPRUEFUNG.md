# Österreich: Umsetzungsprüfung des Worktrees

Stand: 09.09.2026. Prüfgrundlage sind der [Implementierungsplan](superpowers/plans/2026-09-08-austria-compliance-implementation.md), die [Gap-Analyse](OESTERREICH_GAP_ANALYSE.md), `CLAUDE.md`, der vollständige aktuelle Worktree und die darin enthaltenen Tests.

## Ergebnis

Die zuvor reproduzierten P1-Fehler der österreichischen Kernabläufe sind korrigiert. Entwurf, Festschreibung, unveränderlicher Snapshot, GL-Buchung, TaxEvents, Storno, Istbesteuerung, Periodenkontrolle, Steuerabstimmung, amtliche XML-Strukturen, Archivierung und Mandantentrennung werden nun durch Integrationstests abgedeckt.

Der gesamte 18-PR-Plan ist trotzdem noch nicht vollständig freigabefähig. Mehrere erweiterte Fachfälle und Betriebsnachweise fehlen weiterhin. Die bedingten Module RKSV, Bundese-Rechnung und österreichische Personalverrechnung bleiben absichtlich serverseitig gesperrt. Eine Aussage, die App sei bereits ohne fachliche Pilotierung für jeden österreichischen KMU-Fall „einwandfrei“ einsetzbar, wäre daher zu weitgehend.

## Verifikation

| Prüfung | Ergebnis | Aussage |
| --- | --- | --- |
| Vollständige Backend-Suite nach der Fehlerkorrektur | **1.097 bestanden** | Alle AT-Pfade und bestehenden Module sind im gemeinsamen Nachlauf grün. |
| Gezielter Korrekturlauf | 17 bestanden | Kontenrolle, Capability-Gates, Profilrevision, AfA, Rechnungsmerkmale und 4,9-%-Klassifikation. |
| Gesamter AT-Testblock einschließlich Dokumentintegrität | **51 bestanden** | Alle vorhandenen AT-Integrations- und Fachtests sind grün. |
| Alembic auf frischer SQLite-DB | **Upgrade → Downgrade 0088 → Upgrade Head bestanden** | `0089_austria_compliance` ist vorwärts und rückwärts ausführbar. |
| U30, U1 2025 und ZM gegen amtliche BMF-XSDs | **3/3 validiert** | Die erzeugten XML-Dateien entsprechen den geprüften Schemas. |
| Frontend TypeScript | **bestanden** | `npx tsc --noEmit`. |
| Frontend ESLint | **0 Fehler**, 102 Warnungen | Die Warnungen stammen aus dem breiten Bestandsfrontend. |
| Next.js Produktions-Build | **bestanden** | 246 Seiten erzeugt; die vier neuen AT-Routen sind enthalten. |
| Strenger Premium-UI-Audit | **0 Befunde** | Keine unresolved ownership decisions oder statischen UX-Verstöße. |
| PostgreSQL, Restore, Browser-E2E und fachliche Pilotabnahme | offen | Für eine Produktionsfreigabe zusätzlich erforderlich. |

## Behobene Fehler

Die elf Gegenproben aus der ersten Prüfung sind nun geschlossen:

1. AT-Rechnungen und AT-Eingangsrechnungen werden als echte Entwürfe ohne GL-Buchung angelegt.
2. Erst die Festschreibung vergibt die endgültige Nummer und erzeugt GL, Steuerjournal, PDF-Archiv und Snapshot atomar.
3. Unbekannte, falsche oder zeitlich ungültige Steuerbehandlungen blockieren die Festschreibung.
4. Istbesteuerung erzeugt anteilige TaxEvents aus tatsächlichen Zahlungszuordnungen.
5. Stornos erzeugen append-only Gegenereignisse; historische Originalevents bleiben unverändert.
6. Die E/A-Rechnung berücksichtigt zugeordnete Zuflüsse und Abflüsse statt unbezahlter Forderungen und Verbindlichkeiten.
7. Die Basiswährung eines aktiven AT-Mandanten ist nach der ersten Buchung gesperrt.
8. UVA-Finalisierung ist bei Abweichungen zwischen Hauptbuch und TaxEvents gesperrt.
9. Der alte Perioden-Lock-Pfad kann den kontrollierten Close-/Reopen-Ablauf nicht mehr umgehen.
10. Anlagen, Kontenrollen und Archivobjekte werden mandantenbezogen aufgelöst.
11. RKSV, Bundese-Rechnung und Payroll können nicht durch selbst gesetztes Profil-JSON freigeschaltet werden; nur die Deployment-Freigabe `AT_APPROVED_CAPABILITIES` kann den Gate-Check aufheben.

Zusätzlich wurden folgende Fehler im Abschlusslauf korrigiert:

- Lieferverbindlichkeiten sind im AT-Kontenplan konsistent auf Konto 3300 gebunden; Konto 3000 bleibt Rückstellungen vorbehalten.
- Die Halbjahres-AfA und GWG-Sofortabschreibung reduzieren den ausgewiesenen steuerlichen Restbuchwert richtig und werden im Jahreslauf nicht doppelt abgezogen.
- Gleichdatierte Profilkorrekturen erzeugen eine neue Revision und markieren die vorige Revision explizit als superseded; es bleiben keine zwei aktiven Profile übrig.
- Der 4,9-%-Satz wird vor dem 01.07.2026 sowie ohne positive Anlage-3-Klassifikation abgewiesen; Gastronomie wird ausdrücklich genannt.
- Der SQLite-Downgrade entfernt Indizes auf AT-Spalten innerhalb desselben Batch-Umbaus und läuft damit vollständig durch.
- Das gewählte UGB-Geschäftsjahr wird in den Berichtsspalten verwendet.
- Alle Produktformulare besitzen einen anwendungseigenen Validierungsvertrag (`noValidate`); Scrollleisten sind browserübergreifend definiert und leere Scheinlinks entfernt.

## Soll-Ist-Abgleich der 18 Arbeitspakete

| PR | Stand | Bewertung |
| --- | --- | --- |
| 1 – Rechenintegrität und Bankimport | Kern fertig | Locale-Parser, Vorschau-Token, Dateihash und Steuerkonten-Saldierung sind implementiert und getestet. |
| 2 – Beleglebenszyklus | Kern fertig | Invoice, Bill, Credit Note und Debit Note besitzen Festschreibung, Snapshot, Archiv und Korrekturpfad. |
| 3 – Periodensperre | Kern fertig | Close/Reopen, Pflichtgrund, Historie, Saldenhash und Nullergebnis sind getestet. |
| 4 – AT-Profil und Kontenrollen | Kern fertig | GmbH/FlexCo und Einzelunternehmen, UGB/EAR, EUR/de-AT sowie versionierte Profile sind vorhanden. |
| 5 – Rechnungsmerkmale und PDF | Kern fertig | Leistungszeitraum, Parteienmerkmale, Mischsteuersätze, Pflichttexte und geschütztes AT-PDF sind integriert. |
| 6 – Steuerbehandlungen | Kern fertig | 20/13/10/4,9/0, Befreiung, RC, EU und zeitliche Gültigkeit sind versioniert. Erweiterte Übergangsfälle bleiben auszubauen. |
| 7 – Steuerereignisse | Teilweise | Soll-/Istbesteuerung, Teilzahlungen und Korrekturdokumente funktionieren. Anzahlungs-/Schlussrechnungs-Verrechnung, Skonto, Uneinbringlichkeit und TaxAdjustment-Workflows fehlen als vollständige Ereignisketten. |
| 8 – RC/EU/Drittland | Teilweise | Grundfälle, RC-Gegenbuchung, UID-Daten und ZM-Ableitung sind vorhanden. Teilweise/fehlende Vorsteuerberechtigung sowie Nachweis-Review benötigen weitere Golden Cases. |
| 9 – Kleinunternehmer | Kern fertig | 55.000-/60.500-EUR-Grenzen, überschreitender Umsatz, Vorjahr, Hinweis und fünfjährige Optionsbindung sind getestet. |
| 10 – UVA/U1/ZM | Kern fertig | Event-basierte Kennzahlen, Abstimmungssperre, Versionen, Archiv und amtlich validierte XMLs sind vorhanden. Direkte FinanzOnline-Übermittlung ist nicht Bestandteil der Freigabe. |
| 11 – UGB-Bilanz/GuV | Teilweise | §-224-/§-231-Struktur, Vorjahr, negatives Eigenkapital und Checkliste funktionieren. `ReportLineMapping` wird noch nicht als vollständige, versionierte Zuordnungsquelle mit Mapping-Assistent verwendet. |
| 12 – E/A und Nebenbücher | Teilweise | Zahlungsbasierte E/A, E1a-2025-Arbeitsunterlage und Wareneingangsbuch sind vorhanden. Spezielle Zahlungsanteil-Klassifikationen und der EAR→UGB-Wechsel fehlen. |
| 13 – Anlagen-Nebenrechnung | Teilweise | Linear/degressiv, Halbjahresregel, GWG, Vorsteueranteil und Jahreslauf sind vorhanden. UGB-/Steuer-Doppelbasis, Abgang, Teilabgang, Zuschreibung und Vorsteuerberichtigung fehlen. |
| 14 – Archiv und Restore | Teilweise | Physische Dateien, SHA-256, Frist, Attachment-Schutz, mehrere Legal Holds und vollständiger Exportinhalt sind vorhanden. Ein automatisierter Restore und PostgreSQL-PITR-Nachweis fehlen. |
| 15 – Ertragsteuer/Kanzleiexport | Teilweise | 23-%-KSt-Arbeitsblatt, E1a-Daten und gehashter generischer Prüfexport sind vorhanden. Ein Kanzlei-Roundtrip und zielsystemspezifische Golden Files fehlen. |
| 16 – RKSV | Gesperrt | Kein eigener freigegebener RKSV-/DEP-/Signaturadapter; Backend-Gate ist getestet. |
| 17 – Bundese-Rechnung | Gesperrt | Kein abgenommener ebInterface-/e-Rechnung.gv.at-Ablauf; Backend-Gate ist getestet. |
| 18 – Personalverrechnung | Gesperrt | Keine freigegebene AT-Lohnengine/ELDA-Übergabe; Backend-Gate ist getestet. |

## Verbleibende Freigabebedingungen

Vor einem produktiven Compliance-Versprechen sind mindestens folgende Schritte erforderlich:

- Report-Mapping, erweiterte Steuerereignisse, Anlagen-Sonderfälle und Restore wie oben fertigstellen und mit Golden Mandanten prüfen.
- Migration und Parallelzugriffe auf PostgreSQL testen; Backup, Restore und PITR praktisch nachweisen.
- FinanzOnline-Dateien mit amtlichen Beispiel- und Annahmetests für die jeweils eingesetzte Formularversion prüfen. Eine lokal erzeugte Datei ist keine Einreichungsbestätigung.
- UGB-/EStG-/UStG-Ergebnisse durch österreichische Steuerberatung bzw. Wirtschaftsprüfung fachlich abnehmen lassen.
- RKSV, e-Rechnung.gv.at und Personalverrechnung erst nach eigener technischer und fachlicher Abnahme in `AT_APPROVED_CAPABILITIES` freigeben.

Die [Compliance-Matrix](OESTERREICH_COMPLIANCE_MATRIX.md) verwendet `verified` deshalb nur für konkret automatisiert nachgewiesene Kernfähigkeiten und `in_progress` beziehungsweise `blocked` für die verbleibenden Grenzen.
