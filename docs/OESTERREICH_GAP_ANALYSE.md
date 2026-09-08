# Österreich-Anpassung: fachliche und technische Gap-Analyse

Stand: **8. September 2026** · untersuchter Commit: `9501656a`.

Zielgruppe gemäß Rückmeldung: **breite KMU-Unterstützung einschließlich GmbH und Einzelunternehmen**. Untersucht wurde der moderne Stack (`backend/`, `frontend/`) gemäß `CLAUDE.md`; der Express-/Vanilla-JS-Altbestand ist Referenz und kein Ziel der Anpassung.

## Ergebnis und Prüfungsumfang

**Der Fork ist eine brauchbare technische Grundlage, aber derzeit nicht für eine verlässlich österreichische Buchführung und Steuerermittlung einsatzbereit.** Er benötigt ein österreichisches Fachmodell und Korrekturen im gemeinsamen Buchungskern. Sprache, Währung und Steuersätze allein reichen nicht.

Diese Untersuchung verbindet Quellcodeprüfung mit amtlichen Rechts- und Verwaltungsquellen. Sie ist eine technische und fachliche Anforderungsanalyse, keine Bestätigung der Ordnungsmäßigkeit eines konkreten Betriebs. Nicht untersuchte Spezialfälle sind nicht automatisch abgedeckt. Die Quellen wurden am Prüfdatum abgerufen; unterschiedliche Aktualisierungsstände der Informationsseiten wurden berücksichtigt. Insbesondere wurden Steuersatz und UVA-Änderung vom Juli 2026 anhand aktueller RIS-/BMF-Unterlagen geprüft.

Es wurden keine Buchungen, Stammdaten oder Anwendungseinstellungen verändert. Dieses Dokument ist das Arbeitsergebnis. Eine vollständige Backend-/Frontend-Testsuite wurde nicht ausgeführt; im Backend bestand keine lokale `.venv`. Zwei Befunde und eine vorhandene Rechenfähigkeit wurden durch isolierte Ausführung der originalen, per AST extrahierten Funktionen überprüft, ohne App-Start oder Datenbankzugriff:

| Prüfung | Beobachtung |
| --- | --- |
| Bank-CSV mit korrekt zitiertem Wert `"123,45"` | `_parse_csv()` liefert `12345` statt `123.45`: Fehler reproduziert. |
| Reverse Charge, netto 100, Satz 20 %, Steuerkonto gesetzt | Steuerberechnung ergibt 20; Aggregation enthält keine Steuerbuchungszeile. Das ist für den Leistungsbezug unzureichend; der Rechnungsbetrag von 100 ist hingegen richtig. |
| Brutto 104,90 bei 4,9 % | Engine berechnet netto 100,00 und Steuer 4,90 korrekt. Die eigentliche Dezimalrechnung muss dafür nicht neu entwickelt werden. |

Weitere Befunde unten sind statisch aus Code und bestehenden Tests nachvollzogen. Ein fehlender Suchtreffer bedeutet „im geprüften Bestand nicht gefunden“, nicht den Nachweis, dass außerhalb des Repositorys keine externe Lösung existiert.

## Vorhandene Grundlagen und Abweichungen von CLAUDE.md

- [Buchungsservice](../backend/services/posting.py): zentrale Soll-/Haben-Prüfung, Mandantenzuordnung der Konten, Sperre geschlossener Perioden und Buchung nur auf zulässige Konten.
- [Modelle](../backend/models.py): `JournalEntry` besitzt eine Datenbankprüfung gegen negative oder doppelseitige Zeilen. Geldspalten sind bereits `NUMERIC(18,4)` mit `Decimal`; die Float-Angabe in `CLAUDE.md` ist veraltet. An API-Grenzen erfolgt allerdings weiterhin eine Float-Serialisierung; einzelne Module verwenden ebenfalls noch Float-Eingaben.
- [Steuerengine](../backend/services/tax_engine.py): positionsbezogene Steuercodes, Brutto-/Nettorechnung, historische Sätze und gespeicherte Steuerbeträge sind vorhanden.
- [Nummernvergabe](../backend/routers/common.py), Zeile 197: mandantenbezogene Sequenz mit `FOR UPDATE` ist vorhanden. Es handelt sich nicht um ein simples `COUNT(*) + 1`.
- [Perioden](../backend/routers/periods.py): Checklisten, Abschlussbuchung, Salden und Audit-Paket existieren.
- Anlagenbuchhaltung, offene Posten, Gutschriften, Anzahlungen, Fremdwährung, Bankabgleich, Anhänge und Peppol sind vorhandene Ansatzpunkte, deren österreichische Semantik ergänzt werden muss.

Die Architekturhinweise aus `CLAUDE.md` bleiben maßgeblich: Mandantenfilter, zentrale Buchungen, atomare Transaktionen und Alembic-Migrationen. Aussagen über Fachkonformität werden am aktuellen Code überprüft.

## Priorisierte Befunde

**P0** = vor produktiver österreichischer Buchhaltung beheben. **P1** = für den zugesagten KMU-Umfang erforderlich. **Bedingt** = vor Freischaltung des jeweiligen Geschäftsfalls; bei dessen Nutzung ebenfalls ein Freigabehindernis.

| ID | Priorität | Befund und Auswirkung | Konkrete Fundstelle |
| --- | --- | --- | --- |
| AT-01 | P0 | Gebuchte Rechnungspositionen werden beim Editieren gelöscht und ersetzt; das Audit hält nur ausgewählte Kopfdaten, Summen und Positionsanzahl fest. Frühere Leistungsbeschreibungen und Einzelpositionen bleiben so nicht vollständig rekonstruierbar. | [invoices.py](../backend/routers/invoices.py), Z. 694, 724, 896–904, 1096; [bills.py](../backend/routers/bills.py), Z. 502, 630; [Audit-Tests](../backend/tests/test_edit_audit_trail.py) dokumentieren ausdrücklich den Verzicht auf Positionshistorie. |
| AT-02 | P0 | Freie Statusänderung erlaubt `draft`; Bulk-Löschung prüft nur diesen Status, nicht `transaction_id`. Rechnungen werden bereits bei Erstellung gebucht. Damit kann ein Buchungsbeleg verschwinden, obwohl Hauptbuchbewegungen bestehen. Bulk-`void` erzeugt keine Gegenbuchung. | [invoices.py](../backend/routers/invoices.py), Z. 610, 1170, 1255; analog [bills.py](../backend/routers/bills.py), Z. 805, 835. |
| AT-03 | P0 | Steuerbericht zählt Konto `1200` als Vorsteuerkonto, obwohl es im Kontenplan Lagerbestand ist. Außerdem werden dort jeweils nur Haben der Umsatzsteuer bzw. Soll der Vorsteuer summiert; Gegenbuchungen werden nicht saldiert. | [reports.py](../backend/routers/reports.py), Z. 1482–1492; [db.py](../backend/db.py), Z. 405–406. |
| AT-04 | P0 | Reverse Charge unterdrückt Steuerbuchungen gleichermaßen für Verkauf und Einkauf; Erwerbsteuer und abziehbare Gegensteuer werden nicht getrennt erzeugt. | [tax_engine.py](../backend/services/tax_engine.py), Z. 79–126; [bills.py](../backend/routers/bills.py), Z. 282, 416–463. |
| AT-05 | P0 | Kein AT-Steuerprofil; Standardsatz 17 %. Satzermittlung verwendet Rechnungsdatum; Leistungsdatum, Steuerentstehung, Soll-/Ist-Regeln und österreichische Kleinunternehmerlogik fehlen als Fachmodell. | [InvoiceCreate](../backend/routers/invoices.py), Z. 107–119; [Steueraufruf](../backend/routers/invoices.py), Z. 456; [Modelle](../backend/models.py), Z. 611, 1527. |
| AT-06 | P0 | Rechnungsstandard enthält keine vollständigen österreichischen Pflichtangaben; PDF zeigt nur einen Kopfsteuersatz, obwohl Positionen unterschiedliche Sätze haben können. | [invoice.html](../backend/templates/invoice.html), Z. 55–118; [PDF-Kontext](../backend/services/pdf.py), `render_invoice_pdf`; [Parteimodelle](../backend/models.py), Z. 571–610. |
| AT-07 | P0 | Anhänge sind ohne Aufbewahrungs-/Periodenprüfung endgültig löschbar; vollständiges Archiv mit Originalen und Historie nicht vorhanden. | [attachments.py](../backend/routers/attachments.py), Z. 226; [backup.py](../backend/routers/backup.py), Z. 26. |
| AT-08 | P0 | Perioden lassen sich über einfachen Lock-Schalter entsperren und löschen. Beim Lock-Schalter fehlt ein eigener Audit-Eintrag; der separate Reopen-Endpunkt protokolliert hingegen. | [periods.py](../backend/routers/periods.py), Z. 132, 153, `reopen_period`. |
| AT-09 | P0 bei Import | CSV-Import entfernt Dezimalkommas und kann Geldbeträge verhundertfachen. | [bank_imports.py](../backend/routers/bank_imports.py), Z. 59–113. |
| AT-10 | P0 für Steuerberichte | Allgemeiner Steuerbericht nutzt pakistanischen Einkommensteuertarif; CIT-Arbeitsblatt hat 29 % als Vorgabe. Der Bericht nach Steuercodes ist keine österreichische UVA. | [reports.py](../backend/routers/reports.py), Z. 1506, 1537, 2656. |
| AT-11 | P1 | Kontenbaum und Bilanz/GuV sind generisch; AT-Gliederung, Berichtsmapping und E/A-Gewinnermittlung fehlen. Kontonummern werden an zahlreichen Buchungsstellen fest vorausgesetzt. | [db.py](../backend/db.py), `_coa_for`; [reports.py](../backend/routers/reports.py); [periods.py](../backend/routers/periods.py), Konto `3100`. |
| AT-12 | P1 | Abschreibung erfolgt monatlich nach IAS-orientierter Logik, ohne eigenständige österreichische Steuer-AfA. IFRS-16-/IFRS-15-Funktionen sind keine UGB-Bewertungsregeln. | [depreciation.py](../backend/services/depreciation.py), Z. 8; [leases.py](../backend/services/leases.py); [deferred.py](../backend/services/deferred.py). |
| AT-13 | Bedingt | POS besitzt kein gefundenes RKSV-Fachmodell; Peppol ersetzt weder RKSV noch vollständige Bundesrechnungen. | [pos.py](../backend/routers/pos.py); [peppol.py](../backend/services/peppol.py), Z. 101. |
| AT-14 | Bedingt | Lohnmodul bietet allgemeine Gehaltskomponenten, aber keine gefundene österreichische Abgaben-/ELDA-Abwicklung. | [payroll.py](../backend/routers/payroll.py), Z. 36–110. |
| AT-15 | P1 | Sprache erlaubt nur `en`, `ur`, `zh`; Formatierung verwendet `en-PK`. Basiswährung kann durch Settings ohne erkennbare Umrechnung des bestehenden Hauptbuchs geändert werden. | [settings.py](../backend/routers/settings.py), Z. 228–233; [SettingsContext](../frontend/src/context/SettingsContext.tsx), Z. 124, 252–292. |

## Buchführung, Belegintegrität und Aufbewahrung: UGB / BAO

§ 190 Abs. 4 UGB und § 131 BAO verlangen, dass ursprüngliche Aufzeichnungen trotz Änderungen feststellbar bleiben. Die vorhandene Gegenbuchung im Hauptbuch ist dafür ein guter Ansatz; sie ersetzt keine vollständige Belegversion. [RIS: § 190 UGB](https://ris.bka.gv.at/eli/drgbl/1897/219/P190/NOR40069927), [RIS: BAO](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10003940).

**Abgeleitete technische Anforderungen:**

1. Dokumentlebenszyklus trennen: bearbeitbarer Entwurf, festgeschriebener Beleg, nachvollziehbare Korrektur/Storno. Versand- und Zahlungsstatus sind eigene Merkmale. Ein Wechsel des Versandstatus darf keine Buchung löschen oder wieder editierbar machen.
2. Bei Festschreibung vollständige Version speichern: Kopf, Positionen, Adressen, UID, Steuertatbestände, Beträge, Umrechnung, Kontenzuordnung und tatsächlich ausgegebenes PDF/XML. Stammdatenänderungen dürfen alte Rechnungen nicht verändern.
3. Korrektur mit Bezug auf Original, Benutzer, Erfassungszeitpunkt, fachlichem Wirksamkeitsdatum und Begründung. Keine pauschale Rückdatierung: aktuell wird die alte Buchung heute storniert und die Ersatzbuchung möglicherweise zum alten Rechnungsdatum erstellt; das kann die Periodenabstimmung verzerren.
4. Historie auch für Steuercodes, Kontenmapping, Rechnungsnummernregeln, Periodenentsperrung, Archivzugriffe und administrative Datenänderungen. Berechtigungen auf Anwendung und Speicher abstimmen.
5. Nummernvergabe um Datenbank-Eindeutigkeit `(tenant_id, number_series, number)` und Konkurrenztests erweitern. `Invoice` hat aktuell lediglich einen Index auf `number`. Erklärbare Lücken sind zu dokumentieren; eine mathematisch lückenlose Folge ist nicht das alleinige Rechtskriterium. Jahres-/Monatstoken verwenden derzeit das Systemdatum; gewünschte Serienlogik ausdrücklich definieren.
6. Wiederöffnung abgeschlossener Perioden als kontrollierten Vorgang mit Begründung, Berechtigung und Historie ausführen; keine alternative unprotokollierte Entsperrung. Audit-Pakete als unveränderliche Stände versionieren.

Bücher und Belege sind regelmäßig sieben Jahre aufzubewahren, bei einschlägigen anhängigen Verfahren länger. Der Fristbeginn richtet sich nach dem Kalenderjahresende; bei abweichendem Wirtschaftsjahr ist das Kalenderjahr seines Endes maßgeblich. Für Grundstücksunterlagen können längere Fristen bis 22 Jahre greifen. [RIS: BAO § 132](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10003940), [USP: Aufbewahrungspflicht](https://www.usp.gv.at/themen/steuern-finanzen/steuerliche-gewinnermittlung/weitere-informationen-zur-steuerlichen-gewinnermittlung/betriebliches-rechnungswesen/aufbewahrungspflicht.html).

**Archivkonzept:** Aufbewahrungskategorie und Fristende je Beleg, Sperrvermerk für Verfahren, Erhalt der Originaldatei, Inhaltsprüfsumme, Verknüpfung zur Belegversion sowie maschinenlesbarer Export. Speicher-Versionierung bzw. unveränderlicher Speicher sind mögliche technische Maßnahmen, keine hier behauptete gesetzliche Pflicht zu einem bestimmten Produkt oder zu Blockchain. Prüfbarkeit, Lesbarkeit, Wiederherstellung und Schutz vor unbemerkten Änderungen sind nachzuweisen.

Das lokale Backup erfasst SQLite und lokale Uploads; die Anhänge-API speichert dagegen in Supabase. Ein lokales ZIP garantiert deshalb keine Vollständigkeit der Belegdateien. Für PostgreSQL verweist die App auf Plattformbackups. Benötigt werden ein abgestimmtes Sicherungs-/Wiederherstellungsverfahren und ein Exit-Export einschließlich externer Objekte, Metadaten und Historie.

## Rechnungen und österreichische Umsatzsteuer

### AT-Rechnungsmodell

Für eine normale Rechnung gehören insbesondere Aussteller und Empfänger mit Anschrift, Leistungsbeschreibung/-umfang, Leistungsdatum oder -zeitraum, Ausstellungsdatum, fortlaufende Nummer, Entgelt, Steuersatz, Umsatzsteuerbetrag und erforderliche UID-Angaben in die Validierung. Befreiungs- und Reverse-Charge-Hinweise sind fallabhängig. Zusätzliche Unternehmensangaben nach § 14 UGB sind anhand der Rechtsform/Firmenbucheintragung zu behandeln. [USP: Formerfordernisse](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/weitere-informationen-zur-umsatzsteuer/vorsteuerabzug-und-rechnung/formerfordernisse.html), [RIS: UGB](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10001702).

Benötigt werden typisierte Felder für Firmenname, Rechtsform, Sitz, Firmenbuchnummer/-gericht, Steuernummer und UID als getrennte Identifikatoren. Geschäftspartner erhalten Länder-/Adressfelder, Unternehmereigenschaft und UID mit protokolliertem Prüfergebnis. `ntn`/`cnic`/`gstin` und frei definierbare Studio-Felder sind dafür kein belastbarer Ersatz.

**Grenzfälle:** Kleinbetragsrechnungen bis einschließlich 400 Euro brutto haben Erleichterungen, die nicht pauschal auf EU-/RC-Fälle übertragbar sind. Bei mehr als 10.000 Euro brutto ist bei den einschlägigen inländischen B2B-Fällen zusätzlich die Empfänger-UID erforderlich. Allgemeine Rechnungsfrist: sechs Monate; für bestimmte EU-Fälle der 15. des Folgemonats. [USP: Rechnung](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/rechnung.html).

Implementierung: eine gemeinsame serverseitige Fachvalidierung vor Festschreibung, verwendet durch Webformular, Import, API, POS, wiederkehrende Rechnungen und Fachmodule. PDF, Druckansicht und XML greifen auf denselben gespeicherten Stand zu. Steuersummen je Satz/Tatbestand ausweisen; Gestaltungsfreiheit im Template darf notwendige Angaben nicht unbemerkt entfernen.

### Steuersätze und zeitliche Gültigkeit

Das AT-Paket benötigt 20 %, 10 %, 13 % und seit **1. Juli 2026 4,9 % für die Gegenstände der Anlage 3**, mit sachlicher Zuordnung und Gültigkeitsintervallen. Der Satz von 4,9 % gilt nicht allgemein für Lebensmittel oder Gastronomie. Historische Sätze und Sondergebiete/-tatbestände werden nur im jeweils zutreffenden Fall verwendet; Nullsatz, Befreiung und Nichtsteuerbarkeit bleiben unterschiedliche Sachverhalte. [RIS: UStG, § 10 und Anlage 3](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10004873), [BMF: Nahrungsmittel und Übergangsfälle](https://www.bmf.gv.at/rechtsnews/steuern-rechtsnews/aktuelle-infos-und-erlaesse/fachinformationen---umsatzsteuer/umsatzsteuersenkung-auf-ausgewaehlte-nahrungsmittel.html).

Die Engine kann 4,9 % bereits rechnen. Ergänzt werden müssen Artikelklassifikation, Leistungsdatum, historische Tatbestände und Meldeschlüssel. `resolve_rate()` fällt außerhalb gefundener Intervalle auf den aktuellen Satz zurück: im AT-Modus muss ein fehlender gültiger Satz einen fachlichen Fehler auslösen. `prepare_line_taxes()` ignoriert unbekannte/fremde Steuercodes derzeit und kann auf die Kopfsteuer zurückfallen. Vor Festschreibung müssen Existenz, Mandant, Aktivität, Ein-/Ausgangsrichtung und zeitliche Gültigkeit geprüft werden. Jede Position benötigt eine bewusste steuerliche Klassifikation, auch wenn ihre Steuer null ist.

Die Historie muss mehr als den Prozentwert speichern: Befreiungsgrund, Land, Leistungsart, Meldezuordnung und Abzugsquote. Der bestehende Steuerbericht liest Flags aus dem heutigen `TaxCode`; eine Änderung kann damit frühere Auswertungen umklassifizieren.

### Soll-/Istbesteuerung, Anzahlungen und Vorsteuer

Gewinnermittlung und Umsatzsteuerverfahren sind getrennte Entscheidungen. Für die Umsatzsteuer ist je nach Tatbestand Leistungs-, Rechnungs- oder Zahlungszeitpunkt relevant; bei Sollbesteuerung besteht gegebenenfalls die gesetzliche Verschiebung um einen Monat. Vereinnahmte Anzahlungen lösen grundsätzlich bereits vor Leistung Umsatzsteuer aus. [USP: Umsatzsteuerpflicht](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/umsatzsteuerpflicht.html).

Zusätzlich zum Rechnungsdatum erfassen: Leistungszeitraum, Eingangsdatum der Rechnung, Buchungsdatum, Zahlungsereignisse und daraus abgeleitete Steuerperiode. Teilzahlungen benötigen eine nachvollziehbare Verteilung auf Steuerpositionen. Bei einem Verfahrenswechsel sind offene Posten so zu übernehmen, dass keine doppelte oder fehlende Besteuerung entsteht.

Vorsteuer darf nicht allein aus einem positiven Steuersatz folgen. Bei bestimmten Istbesteuerern bis zwei Millionen Euro maßgeblichem Vorjahresumsatz ist die Zahlung zusätzliche Voraussetzung; gesetzliche Ausnahmen sind gesondert abzubilden. Teilweise/nicht abzugsfähige Vorsteuer und spätere Berichtigungen benötigen eigene Beträge und Nachweise. [USP: Vorsteuerabzug](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/vorsteuerabzug.html).

Der [Anzahlungsprozess](../backend/routers/advances.py) bucht derzeit nur Bank gegen Anzahlungskonto. Er benötigt steuerliche Klassifikation, Anzahlungsrechnung, Vereinnahmungssteuer und Schlussrechnungsabzug. Rabatte, Skonto, Retouren und Uneinbringlichkeit brauchen positionsbezogene Steuerberichtigungen; [credit_notes.py](../backend/routers/credit_notes.py) nimmt bislang einen manuellen Gesamtsteuerbetrag entgegen. Berichtigungen beziehen sich auf die ursprüngliche Besteuerung, nicht einfach auf den aktuell gültigen Satz. [RIS: UStG § 16](https://www.ris.bka.gv.at/GeltendeFassung.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10004873).

### Reverse Charge und EU-Geschäfte

Beim steuerpflichtigen Leistungsbezug mit Übergang der Steuerschuld schuldet der Empfänger die Umsatzsteuer und kann sie bei Vorliegen der Voraussetzungen als Vorsteuer abziehen. Der Lieferant erhält weiterhin nur den Nettobetrag. [USP: Reverse Charge](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/weitere-informationen-zur-umsatzsteuer/umsaetze-mit-auslandsbezug/reverse-charge.html).

**Abgeleiteter Buchungstest:** EU-Dienstleistung 100 Euro, österreichischer Satz 20 %, voller Vorsteuerabzug: Aufwand 100 / Verbindlichkeit 100 sowie Vorsteuer RC 20 / Umsatzsteuer RC 20. Ohne Abzugsrecht erhöht die nicht abziehbare Steuer den Aufwand bzw. die Anschaffungskosten. Das gegenwärtige gemeinsame RC-Flag kann diese Unterscheidung nicht ausdrücken.

Eigene Tatbestände für inländische RC-Fälle, EU-B2B-Dienstleistungen, innergemeinschaftlichen Erwerb, innergemeinschaftliche Lieferung, Ausfuhr und Einfuhrumsatzsteuer anlegen. UID-Prüfung und Liefer-/Ausfuhrnachweise speichern. EU-Dienstleistungen nach der Grundregel können in die ZM gehören; nicht jede grenzüberschreitende Leistung tut dies. [USP: grenzüberschreitende Dienstleistungen](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/weitere-informationen-zur-umsatzsteuer/umsaetze-mit-auslandsbezug/grenzueberschreitende-dienstleistungen.html).

OSS/IOSS, Versandhandel, Dreiecksgeschäfte, Differenzbesteuerung, Gutscheine und branchenspezifische Befreiungen benötigen zusätzliche, gesondert spezifizierte Regeln vor Aktivierung. Ein pauschales „EU + UID = Reverse Charge“ ist keine ausreichende Fallentscheidung.

### Kleinunternehmer

Seit 2025 gilt grundsätzlich die Grenze von **55.000 Euro** im laufenden und vorangegangenen Kalenderjahr. Bis 10 % Überschreitung kann die Befreiung im Überschreitungsjahr fortwirken; bei mehr als 10 % entfällt sie bereits für den überschreitenden und die folgenden Umsätze. Die Berechnung berücksichtigt gesetzliche Ausnahmen; ein bloßes Summieren aller Rechnungsbeträge genügt nicht. Auch Verzicht und Bindungszeit sowie gegebenenfalls das EU-Kleinunternehmerverfahren gehören zum Profil. [USP: Kleinunternehmen](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/weitere-informationen-zur-umsatzsteuer/weitere-steuertatbestaende-und-befreiungen/kleinunternehmen.html).

Implementierung: datierte Statushistorie, überwachte maßgebliche Umsätze beider Jahre, Warnung vor Grenzüberschreitung, nachvollziehbarer Wechsel und Befreiungshinweis. Eine Kleinunternehmerbefreiung beseitigt nicht automatisch jede Steuerschuld aus Leistungsbezügen. Auch GmbH und E/A-Status dürfen nicht als Synonym für einen Umsatzsteuerstatus verwendet werden.

## UVA, Jahreserklärung und Steuerberaterübergabe

Der bestehende Bericht `/tax-return` aggregiert Rechnungs-/Eingangsrechnungspositionen nach Rechnungsdatum. Er berücksichtigt in dieser Abfrage weder Gutschriften noch Zahlungssteuerereignisse oder Journalberichtigungen; er hat keinen Filter auf steuerlich relevante Festschreibungszustände. Die Positionsbeträge werden zudem ohne erkennbare gemeinsame EUR-Umrechnung summiert. Er ist deshalb keine Grundlage für eine AT-Meldung ohne Umbau.

**Zielmodell:** ein unveränderliches Steuerjournal aus festgeschriebenen Geschäftsvorfällen, mit Beleg-/Positionsbezug, Bemessungsgrundlage in EUR, Steuerbetrag, Abzugsquote, Steuerperiode und versioniertem Meldeschlüssel. Daraus entstehen UVA, U1, ZM sowie die Abstimmung gegen das Hauptbuch. Korrekturmeldungen behalten Bezug und Differenz zur ursprünglichen Meldung.

UVA: über 100.000 Euro maßgeblichem Vorjahresumsatz grundsätzlich monatlich, über 55.000 bis 100.000 Euro grundsätzlich vierteljährlich; darunter sind Ausnahmen, Wahlrechte und behördliche Anordnungen zu beachten. Regeltermin ist der 15. des zweitfolgenden Monats. [USP: Umsatzsteuervoranmeldung](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/weitere-informationen-zur-umsatzsteuer/entstehen-der-steuerschuld-und-pflichten/umsatzsteuervoranmeldung.html).

Ab Juli bzw. dem dritten Quartal 2026 enthalten die UVA-Unterlagen die neuen Kennzahlen **124 und 125**. Exportversionen müssen deshalb nach Meldezeitraum gewählt werden. [BMF: Dokumentenversion UVA ab 07/2026](https://www.bmf.gv.at/dam/jcr%3A922a2cf9-e758-40c4-a671-1674044cced1/BMF_Dokumentenversion_UVA%20ab_07_2026.pdf).

Zunächst nachvollziehbare Kennzahlenauswertung und validierbaren XML-Dateiexport entwickeln. Eine spätere direkte FinanzOnline-Übermittlung braucht die veröffentlichten Strukturen, Authentifizierung, Berechtigungen, technische Prüfungen, Rückmeldungen und Wiederholungslogik. Ein exportiertes oder abgesendetes Dokument ist noch keine bestätigte Einreichung. [BMF: Datenstromübermittlung](https://www.bmf.gv.at/services/finanzonline/informationen-fuer-softwarehersteller/datenstromuebermittlung.html).

BMD-/RZL-/andere Kanzleiexporte sind praktische Integrationen, keine allgemeine Pflicht zu einer bestimmten Marke. Format mit der empfangenden Kanzlei festlegen; liefern sollten sie zumindest Buchungsdatum, Belegdatum/-nummer, Konto/Gegenkonto, Betrag/Währung, Steuerschlüssel, Personenkonto und Belegverknüpfung. Ein frei konfigurierbarer CSV-Bericht ersetzt keinen vollständigen Prüfungs- und Migrationsbestand.

## UGB-Abschluss, Kontenplan und E/A-Rechnung

Kapitalgesellschaften unterliegen grundsätzlich unabhängig vom Umsatz der UGB-Rechnungslegung. Für einschlägige Einzelunternehmen/Personengesellschaften gelten die Schwellen von mehr als 700.000 Euro in zwei aufeinanderfolgenden Jahren mit Pufferjahr bzw. mehr als einer Million Euro einmalig mit Wirkung im Folgejahr; gesetzliche Ausnahmen, etwa für freie Berufe, sind zu beachten. [USP: Buchführungspflicht](https://www.usp.gv.at/themen/steuern-finanzen/steuerliche-gewinnermittlung/weitere-informationen-zur-steuerlichen-gewinnermittlung/betriebliches-rechnungswesen/buchfuehrungspflicht-und-buchfuehrung.html).

Ein AT-Onboarding benötigt mindestens Rechtsform, Tätigkeit, Gewinnermittlungsart, Umsatzsteuerverfahren, Vorjahreswerte, Wirtschaftsjahr, Größenklasse und verpflichtende Module. Das sind getrennte Merkmale. Bei Grenzübertritt oder Rechtsformwechsel ist eine datierte Migration erforderlich.

**Kontenmodell:** österreichischen Kontenplan als anpassbare Vorlage einführen. Österreichisches Recht schreibt nicht pauschal eine bestimmte vierstellige Kontonummer vor. Die gesetzlichen Ausweise müssen aus Konten eindeutig ableitbar sein. Statt `1200`/`2200`/`3100` fest in Buchungscode einzubauen, semantische Rollen wie Lager, Umsatzsteuer, Vorsteuer, Kapital und Ergebnisvortrag verwenden. Änderungen bestehender Nummern brauchen Mappings; bereits gebuchte Daten dürfen nicht durch Neueinsaat umgedeutet werden.

Für GmbH-Berichte die Bilanzgliederung nach § 224 UGB und GuV nach § 231 UGB abbilden; anwendbare Größenklassenerleichterungen, Vorjahresvergleich, Anhang und gegebenenfalls Lagebericht berücksichtigen. Rückstellungen, Abgrenzungen, Inventur und Bewertung müssen in den Abschlussprozess einfließen. Offenlegung ist grundsätzlich spätestens neun Monate nach Abschlussstichtag zu erledigen. [RIS: § 224 UGB](https://ris.bka.gv.at/eli/drgbl/1897/219/P224/NOR40181521), [RIS: § 231 UGB](https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10001702&Paragraf=231&FassungVom=2026-09-08), [RIS: § 277 UGB](https://ris.bka.gv.at/eli/drgbl/1897/219/P277/NOR40275593).

Die IFRS-Funktionen dürfen im UGB-Einzelabschluss nicht ungeprüft Bewertungsbuchungen erzeugen. Insbesondere IFRS-16-Nutzungsrechte, IFRS-15-Vertragsvermögen und konzernbezogene IFRS-Regeln brauchen eine gesonderte Zuordnung bzw. Nebenrechnung. Bewertungsgrundlage und Bericht müssen zusammenpassen. [RIS: UGB-Bewertungsgrundsätze, § 201](https://www.ris.bka.gv.at/NormDokument.wxe?Abfrage=Bundesnormen&Gesetzesnummer=10001702&Paragraf=201&FassungVom=2026-09-08).

**Zusätzlicher Kernbefund:** `close_period()` bucht nur positive Normalsalden um und überspringt die Abschlussbuchung vollständig, wenn der Nettogewinn null ist. Für gleich hohe Erlöse und Aufwendungen sowie negative Erlös-/Aufwandskontensalden braucht es gezielte Abschlussprüfungen. Monatsabschluss, Jahresabschluss und Wiederöffnung dürfen den für die GuV relevanten Datenbestand nicht verfälschen.

**Einnahmen-Ausgaben-Rechnung:** eigener Bericht nach Zufluss/Abfluss einschließlich steuerlicher Ausnahmen, Privatanteilen, Einlagen/Entnahmen, nicht abzugsfähigen Ausgaben, Anlagenverzeichnis und gegebenenfalls Wareneingangsbuch. E1a-/E1a-K-Zuordnung vorsehen. Eine Cashflow-Auswertung oder das Geschäftsmodell `simple` erfüllt diese Anforderungen nicht automatisch. Der gemeinsame doppelte Buchungskern kann bleiben; die fachliche Gewinnermittlung muss zahlungsbezogen erfolgen. [USP: Einnahmen-Ausgaben-Rechnung](https://www.usp.gv.at/themen/steuern-finanzen/steuerliche-gewinnermittlung/einnahmen-ausgaben-rechnung.html).

## Anlagen und Ertragsteuern

Separate handelsrechtliche und steuerliche Wertentwicklung je Anlage vorsehen. Das bestehende Modell liefert einen Ausgangspunkt, aber der Monatsbetrag allein bildet die österreichische Steuer-AfA nicht ab. Nach § 7 EStG ist für die Halbjahresregel grundsätzlich die Nutzung von mehr als sechs Monaten im Wirtschaftsjahr maßgeblich; das reine Anschaffungsdatum genügt nicht. Degressive AfA erfordert gesetzliche Voraussetzungen und einen zulässigen Satz. [RIS: § 7 EStG](https://ris.bka.gv.at/eli/bgbl/1988/400/P7/NOR40225593).

GWG bis 1.000 Euro können unter den Voraussetzungen sofort abgeschrieben werden; die relevante Kostenbasis hängt auch vom Vorsteuerabzug ab. Bei E/A ist für die Sofortabschreibung das Zahlungsjahr maßgeblich, bei Buchführung grundsätzlich das Anschaffungs-/Herstellungsjahr. [USP: GWG](https://www.usp.gv.at/themen/steuern-finanzen/steuerliche-gewinnermittlung/weitere-informationen-zur-steuerlichen-gewinnermittlung/betriebseinnahmen-und-ausgaben/geringwertige-wirtschaftsgueter.html).

Anlagekategorien, Inbetriebnahme, Nutzungsdauer, betrieblicher Anteil, Sonderregeln für Gebäude/Fahrzeuge, Abgang, Zuschreibung und Vorsteuerberichtigung benötigen dokumentierte Entscheidungen. Investitions-/Gewinnfreibeträge und Pauschalierungen sind gesonderte, jahresabhängige Fachfunktionen; keine Ableitung aus einem generischen AfA-Satz.

Der pakistanische Tarif muss für AT deaktiviert und durch jahresbezogene österreichische Logik ersetzt werden. Körperschaftsteuer nach § 22 KStG beträgt grundsätzlich 23 %; die Bemessungsgrundlage ist steuerliches Einkommen und nicht einfach der Bilanzgewinn. [USP: Körperschaftsteuer](https://www.usp.gv.at/services/suchen-und-finden/lexikon/koerperschaftsteuer.html).

Für Einzelunternehmen braucht es EStG-Tarife des betreffenden Jahres und eine klare Trennung zwischen betrieblichem Ergebnis und persönlicher Einkommensteuer. Für Gesellschaften gehören steuerliche Mehr-/Weniger-Rechnung, Verlustvorträge und gegebenenfalls Mindeststeuer zur späteren Steuerfunktion. Bis diese vollständig spezifiziert ist, korrekte Buchhaltungs-/Kanzleidaten bereitstellen und keine irreführende AT-Steuerschätzung anzeigen.

## Bedingte Erweiterungen

### Bargeschäft und Registrierkasse

Bei Überschreiten von 15.000 Euro Jahresumsatz und 7.500 Euro Barumsatz besteht grundsätzlich Registrierkassenpflicht; betriebliche Zuordnung, Beginn der Pflicht und Ausnahmen sind zu prüfen. Für diesen Zweck können auch Kartenzahlungen Barumsätze sein. Belegerteilung und Registrierkassenpflicht sind getrennte Pflichten. [USP: Registrierkassenpflicht](https://www.usp.gv.at/themen/steuern-finanzen/steuerliche-rechte-und-pflichten/registrierkassen.html), [BMF: Registrierkasseninformationen](https://www.bmf.gv.at/en/topics/taxation/cash-register/cash-register-receipt-issuing-obligation.html).

Vor AT-Kassenfreigabe benötigt das POS-Modul einen RKSV-Adapter mit Signatur-/Siegelerstellung, Verkettung, Datenerfassungsprotokoll, Belegmerkmalen, Start-/Monats-/Jahresbelegen, Ausfallbehandlung sowie Registrierung und Prüfung. Alternative: Integration einer entsprechend ausgelegten externen Kasse und nachvollziehbare Übernahme. Die technische Umsetzung muss sich an den aktuellen BMF-Vorgaben einschließlich 4,9-%-Behandlung orientieren. [BMF: Registrierkassenerlass vom Juni 2026](https://findok.bmf.gv.at/findok/volltext?segmentId=c953d962-d9bb-4e71-8be4-e5ee005e94ab).

Bereits angekündigte Umstellung berücksichtigen: **ab 1. Oktober 2026** gelten Erleichterungen für digitale Belegmitnahme einschließlich Anspruch auf Papierbeleg. Das ist am Prüfdatum noch nicht in Kraft. [BMF: digitale Belegmitnahme](https://www.bmf.gv.at/public/top-themen/Elektronischer-Beleg-und-digitale-Belegmitnahme-.html).

### Elektronische Rechnungen und Bund

Für Lieferungen/Leistungen an Bundesdienststellen sind strukturierte elektronische Rechnungen vorgesehen. Eine allgemeine österreichische Pflicht, sämtliche B2B-Rechnungen nach deutschem XRechnung-Regime zu verarbeiten, lässt sich daraus nicht ableiten. [USP: Rechnung / e-Rechnung](https://www.usp.gv.at/themen/steuern-finanzen/umsatzsteuer-ueberblick/rechnung.html).

e-Rechnung.gv.at unterstützt ebInterface und UBL; über Peppol ist UBL vorgesehen. Auftragsreferenz und weitere empfängerabhängige Angaben benötigen eine eigene Prüfung. [e-Rechnung.gv.at: Formate](https://www.erechnung.gv.at/erb/tec_formats), [Bundesspezifische ebInterface-Regeln](https://www.erechnung.gv.at/erb/tec_formats_ebinterface).

Der vorhandene Peppol-Builder verwendet `ntn`/`gstin` als Käufer-ID und leitet aus Käufer-ID plus Nullsatz automatisch RC ab. Das ist fachlich falsch für zahlreiche steuerfreie Lieferungen. Kategorien und Summen müssen aus den gespeicherten Tatbeständen entstehen. Echte Schema-/Geschäftsregelvalidierung, Bundesreferenzen, Originalarchiv und Empfangsprotokoll sind vor einer Zusage zur Nutzbarkeit notwendig. Ein XML mit BIS-Kennung allein ist kein Konformitätsnachweis.

### Personalverrechnung

Für in der App berechnete AT-Löhne werden unter anderem Lohnkonto, Lohnsteuer, Sozialversicherung, Sonderzahlungen, kollektivvertragliche Regeln, Kommunalsteuer und weitere Dienstgeberabgaben benötigt. Das allgemeine Gehaltskomponentenmodell deckt dies nicht als österreichisches Regelwerk ab. [USP: Aufgaben der Lohnverrechnung](https://www.usp.gv.at/themen/mitarbeiter-und-gesundheit/entgelt/die-wichtigsten-aufgaben-der-lohnverrechnung.html).

mBGM wird über ELDA übermittelt. Für eine frühe KMU-Version ist der Import geprüfter Lohnbuchungsbelege aus einer vorhandenen Lohnverrechnung eine tragfähige Abgrenzung; wer vollständige Personalverrechnung anbietet, benötigt einen separaten Entwicklungs- und Validierungsumfang. [USP: mBGM](https://www.usp.gv.at/themen/mitarbeiter-und-gesundheit/entgelt/monatliche-beitragsgrundlagenmeldung.html).

## Lokalisierung, Banking und Betrieb

- **Deutsch/Österreich:** `de-AT`, EUR, Zeitzone `Europe/Vienna`, Dezimalkomma und verständliche deutsche Fachbegriffe zentral bereitstellen. Die in `CLAUDE.md` verlangten gemeinsamen Datums-/Betragshilfen weiterverwenden und dort parametrieren. Zweistellige Jahreszahlen und `dd-mm-yy` sind eine Produktkonvention, keine österreichische Rechtsvorgabe.
- **Währungswechsel:** EUR für neue AT-Mandanten setzen. Bei bestehenden Buchungen einen Wechsel der Basiswährung sperren oder über eine fachlich geprüfte Migration ausführen; bloßes Ändern des Währungsetiketts ist falsch. Umrechnungskurs, Quelle und Datum für Steuer- und Buchungszwecke nachvollziehbar speichern.
- **Bankimport:** explizite CSV-Profile für Trennzeichen, Dezimal-/Tausenderzeichen und Datum; mehrdeutige Beträge ablehnen. Vorschau und Summenkontrolle vor Übernahme. camt.053/054 und SEPA-Export sind sinnvolle zusätzliche Integrationen, keine allgemeine Buchführungspflicht. Vorhandener `openbanking.py`-Adapter verarbeitet Sandbox-/JSON-Daten und ist noch kein nachgewiesener Live-Anschluss an österreichische Banken.
- **Mandantentrennung:** neue Steuerereignisse, Einstellungen, Dokumentversionen und Exporte müssen die vorhandene Tenant-Grenze fortsetzen. Der SQLite-Backup-Endpunkt exportiert die gesamte Datenbank; bei Mehrmandantenbetrieb ist ein Tenant-Admin dafür keine geeignete Instanzberechtigung.
- **Datenschutz:** Verarbeitung von Kunden-, Mitarbeiter- und gegebenenfalls Gesundheitsdaten benötigt passende Rechtsgrundlagen, Auftragsverarbeitung, Zugriffsschutz und Lösch-/Aufbewahrungskonzept. KI-Provider, Speicher und Bankdienste in die Empfänger-/Transferprüfung einbeziehen; Buchführungsaufbewahrung nicht durch eine pauschale Löschfunktion unterlaufen. Maßgeblich sind insbesondere DSGVO Art. 5, 6, 17 Abs. 3, 28, 32 und gegebenenfalls 44 ff. [EUR-Lex: DSGVO](https://eur-lex.europa.eu/eli/reg/2016/679/oj/deu).

## Umsetzungsvorschlag

Das AT-Paket sollte eine klar abgegrenzte Erweiterung des modernen Stacks sein. Fehler wie Belegverlust, falsche Steuerkonten oder falsches CSV-Parsing gehören zusätzlich in den gemeinsamen Kern.

| Phase | Konkretes Ergebnis | Abhängigkeit / Abschlusskriterium |
| --- | --- | --- |
| 1. Integrität und akute Fehler | AT-01 bis AT-04, AT-07 bis AT-09; Statusmaschine, vollständige Versionen, kontrollierte Perioden und korrektes Parsing. | Keine veröffentlichte/gebuchte Rechnung durch Statuswechsel löschbar; Ursprungsbeleg bleibt vollständig verfügbar. |
| 2. AT-Fachmodell | Modul `at_accounting`, datierte Mandantenprofile, Rollen im Kontenplan, AT-Steuerkatalog und Partei-/Rechnungsfelder. | Keine 17-%-Fallbacks im AT-Profil; Besteuerung und Gewinnermittlung getrennt konfigurierbar. |
| 3. Steuerereignisse und Rechnungen | Soll/Ist, Anzahlungen, Korrekturen, RC/Erwerb, Vorsteuerquoten, KU-Regeln und AT-PDF. | Rechnung → Steuerjournal → Hauptbuch stimmen für die Testfälle überein. |
| 4. Meldungen und beide Gewinnermittlungsarten | UVA/U1/ZM-Vorbereitung, E/A mit E1a-Zuordnung, UGB-Abschlussmapping, Anlagen-Nebenrechnung und Kanzleiexport. | Freigegebene Beispielmandanten GmbH und Einzelunternehmen liefern abstimmbare Ergebnisse. |
| 5. Bedingte Module | RKSV oder externe Kasse, Bundesrechnung/Peppol, Banking und Lohnintegration. | Freigabe je Geschäftsfall mit passenden externen Validatoren und Rückmeldungen. |

**Vorgeschlagene neue Bausteine** (noch nicht implementiert): `backend/localizations/at/` für datierte Regeln/Mapping, `TaxEvent`, `DocumentVersion`, `RetentionPolicy` und ein AT-Profil mit `accounting_method`, `vat_method`, `vat_exemption_status`, Rechtsform, Wirtschaftsjahr und Gültigkeitszeitraum. Die bestehenden `TaxCode`-/`TaxRateHistory`-Modelle weiterverwenden und erweitern. Kontenrollen und Buchungsservice gemeinsam halten.

Migrationen über Alembic, einschließlich SQLite-kompatibler Schritte. Bestehende Daten zunächst inventarisieren: gebuchte Entwürfe, fehlende Originale, historische Kopfsteuer, unvollständige Steuercodes und falsch importierte Beträge. Solche Altdaten nicht stillschweigend als AT-konform kennzeichnen. Fehlende historische Beleginhalte können aus einer Migration allein nicht wiederhergestellt werden. Überleitung mit Eröffnungssalden, offenen Posten, Anlagen, Steuerpositionen und Archivabgleich dokumentieren.

## Verbindliche Abnahmefälle für die Umsetzung

1. Normalrechnung mit 20 %, 10 %, 13 % und 4,9 %: identische, nachvollziehbare Werte in API, PDF, Buchung und Steuerjournal.
2. Lieferung eines begünstigten Produkts am 30.06.2026, Rechnung im Juli: alter Satz; Lieferung ab 01.07.: neuer Satz. Rückabwicklung der Junilieferung im Juli korrigiert den ursprünglichen Satz.
3. Rechnungsbeträge 400,00 / 400,01 / 10.000,00 / 10.000,01 Euro: richtige Pflichtfeldregeln einschließlich B2B-/Länderkontext.
4. RC-Eingang 100 Euro: 20 Euro Steuerschuld bei Satz 20 %, volle/teilweise/keine Vorsteuer je Berechtigung; Verbindlichkeit bleibt 100 Euro.
5. Teilzahlung bei Istbesteuerung, unbezahlte Rechnung bei Sollbesteuerung, Anzahlungs- und Schlussrechnung: richtige Periode ohne doppelte Steuer.
6. KU-Umsätze an den Grenzen 55.000 / 60.500 Euro und darüber, mit Vorjahr, Ausnahmen und überschreitendem Einzelumsatz.
7. Artikelbeschreibung oder UID nach Festschreibung ändern: Originalversion, Ausdruck und Historie bleiben erhalten.
8. Gebuchter Beleg → Status `draft` → Bulk-Löschung: abgelehnt; Storno erzeugt Gegenbuchung und Steuerkorrektur mit Originalbezug.
9. Lagerzugang 1.000 Euro: niemals 1.000 Euro Vorsteuer im Steuerbericht. Stornierte Steuerbeträge werden saldiert.
10. CSV-Werte `123,45`, `1.234,56`, `1,234.56`, negatives Vorzeichen und verschiedene Trennzeichen: korrekte Profile oder klarer Fehler, keine stille Umdeutung.
11. Abschluss mit Gewinn null, Verlust und negativen Kontensalden; Wiederöffnung/erneuter Abschluss ohne doppelte Ergebnisumbuchung.
12. EUR-Auswertung von Fremdwährungsbelegen, Rundungsdifferenzen und dokumentierten Kursen; Währungswechsel bei bestehenden Buchungen geschützt.
13. Archivexport einschließlich Supabase-Originalen und vollständige Wiederherstellung; Löschung während Aufbewahrungsfrist oder Verfahrenssperre verhindert.
14. UVA vor/nach Juli 2026, mit RC, Erwerb, Gutschrift und Fremdwährung: richtige Kennzahlen, gültige Struktur und Hauptbuchabstimmung.
15. Mandantenübergreifende IDs in Steuercodes, Versionen, Archiv und Export: kein Datenzugriff oder stiller Steuerfallback.

Die fachliche Endabnahme sollte anhand dieser Fälle mit österreichischer Steuerberatung/Bilanzbuchhaltung erfolgen. Besonders kundenspezifisch bleiben Branchenbefreiungen, Pauschalierungen, Grundstücke, Fahrzeugbesteuerung, Personalverrechnung und grenzüberschreitende Sonderfälle. Die breite KMU-Version kann sie über klar benannte Module bzw. geprüfte externe Übergaben abdecken.
