# Fluer Development — Design System

Fluer Development ist ein Einzelunternehmen mit Schwerpunkt **Cloud-App-Entwicklung**: Architektur, Umsetzung und Betrieb von Web-Anwendungen aus einer Hand. Ein Ansprechpartner, kleine Kundenteams, EU-Hosting.

Dieses Design System deckt zwei Flächen ab:

1. **Marketing-Website** — öffentliche Einzelseite (Hero, Leistungen, Arbeit, Kontakt).
2. **Cloud Console** — Produktfläche für Projekte, Deployments, Logs, Einstellungen.

## Quellen

Für diesen Auftrag lagen **keine** externen Quellen vor: kein Figma-File, kein Repository, kein Codebase-Mount, keine Screenshots, keine Fontdateien, keine Logodatei, keine bestehende Website. Die Grundlage war ausschließlich die schriftliche Kurzbeschreibung:

> „Fluer Development — Einzelunternehmen, Schwerpunkt Cloud App Entwicklung. Clean, aber nicht steril; viel Whitespace; klare visuelle Hierarchie; wenige, gezielt eingesetzte Farben; subtile statt auffällige Effekte; eher ruhige Oberflächen als ‚Dashboard voller Karten'; starke Typografie; leichte Tiefenwirkung durch Border, Blur und Shadow; abgerundete Ecken, aber nicht alles als ‚Pill'."

Alles Visuelle unten ist daraus abgeleitet, nicht rekonstruiert. **Zwei Substitutionen sind zu bestätigen** (siehe „Offene Punkte").

## Content Fundamentals

**Sprache.** Deutsch, Sie-Form. Kundenansprache im Marketing („Sie sprechen mit der Person, die Ihre Anwendung baut"), in der Console dagegen unpersönlich und sachlich (Objekte und Zustände, keine Anrede: „Deployment erfolgreich", nicht „Ihr Deployment war erfolgreich!").

**Ich vs. wir.** Es gibt kein „wir". Das Unternehmen ist eine Person: „Ich" im Marketing-Fließtext, „Fluer Development" als Absender. Nie Plural-Fassade.

**Tonfall.** Nüchtern, konkret, prüfbar. Zahlen und Fakten statt Adjektiven: „24 ausgelieferte Anwendungen", „Antwort innerhalb eines Werktags", „Erstgespräch, 30 Minuten, ohne Kosten". Keine Superlative, keine Agentursprache („ganzheitlich", „maßgeschneidert", „innovativ"), keine Ausrufezeichen.

**Casing.** Satzschreibung überall — Überschriften, Buttons, Tabellenköpfe. Kein Title Case. Uppercase ausschließlich im Eyebrow-Label (12px, 0.1em Laufweite, z. B. `LEISTUNGEN`).

**Button-Labels.** Verb + Objekt, maximal drei Wörter: „Projekt anfragen", „Deploy starten", „Endgültig löschen". Nie „Los geht's", nie „Mehr erfahren" ohne Objekt.

**Fehler und Zustände.** Was passiert ist, dann was zu tun ist. „Build fehlgeschlagen — Schritt 3: typecheck" + Aktion „Log öffnen". Keine Schuldzuweisung, keine Entschuldigungsfloskeln.

**Technische Werte** stehen in Mono: `eu-central-1`, `deploy_8f2c41`, `128 ms`, `main`. Deutsche Zahlenformate im Fließtext (99,98 %, 1,4 Mio., 84 €).

**Emoji: nein.** Nirgends — nicht in UI, nicht in Marketing, nicht in Statusmeldungen. Zustand wird über Badge-Farbe und Lucide-Icon ausgedrückt.

## Visual Foundations

**Farbe.** Ein einziger Akzent: Deep Blue `#17518C` (`--blue-500`). Er erscheint auf dem Primary-Button, im Fokusring, im Tab-Indikator, im Logo-Zeichen und in kleinen Icon-Flächen (`--blue-50` Fläche + `--blue-200` Rand) — sonst nirgends. Die Flächen tragen warme Papiergrau-Töne (`--n-25` Seite, `--n-0` Karte); reines Kaltgrau kommt nicht vor. Semantische Farben (Moss, Amber, Rot, Petrol) sind ausschließlich Zustandsfarben, nie Dekoration. Maximal zwei Hintergrundflächen pro Seite (`--bg-page` und `--bg-page-alt`), plus genau ein dunkler Block (`--n-900`) als Abschluss oder Kontrastfläche.

**Typografie.** Geist (Sans) für alles, Geist Mono für IDs, Regionen, Commits, Logs und Tabellenzahlen. Display und Headings in Semibold (600) mit negativer Laufweite (−0.026em / −0.014em) — der visuelle Hauptreiz ist große, engstehende Typografie auf leerer Fläche, nicht Farbe. Fließtext 16px/1.5 auf maximal 68ch, UI-Text 14px. Light (300) wird nicht verwendet, Bold (700) nur in Ausnahmen.

**Layout und Weißraum.** Container 1280px, Gutter 32px, Sektionsabstand 96px, Hero-Oberkante 128px. Innerhalb einer Karte: 24px Padding, 8px zwischen Titel und Text, 32px zwischen Blöcken. Weißraum ist das primäre Gestaltungsmittel — wenn eine Fläche leer wirkt, wird Inhalt geschärft, nicht Füllmaterial ergänzt. Fixiert sind nur zwei Elemente: die Website-Kopfzeile (sticky, Glass) und die Console-TopBar.

**Karten und Tiefe.** Tiefe entsteht in dieser Reihenfolge: Haarlinie (`--border-hairline`) → weicher Schatten (`--shadow-sm`) → Blur. Nie Schatten ohne Rand. Standardkarte: weiß, 1px Rand, 14px Radius, `--shadow-sm`. Klickbare Karten heben auf `--shadow-md` und einen etwas stärkeren Rand — keine Bewegung, kein Scale. Eingesenkte Bereiche (Logs, Vorschau) nutzen `--surface-sunken` ohne Schatten. Listen und Tabellen sind bewusst _keine_ Kartenraster: eine umrandete Fläche mit Haarlinien-Zeilen.

**Radien.** 3px (Badge, Checkbox), 6px (IconButton, kleine Buttons), 10px (Buttons, Felder), 14px (Karten), 20px (Dialog), 28px (dunkler Abschlussblock). Pill (999px) nur bei Tag, Switch und Avatar — nie bei Buttons.

**Transparenz und Blur.** Genau drei Einsätze: sticky Kopfzeilen (`--surface-glass`, 72 % Weiß + 14px Blur), Toasts (gleiche Glasfläche, stärkster Schatten der Skala) und der Dialog-Scrim (`rgba(22,22,20,.36)` + 3px Blur). Blur ist ein Hinweis auf „schwebt über der Seite" — keine dekorativen Glaskarten im Content.

**Animation.** 90–320ms, `cubic-bezier(.2,.6,.2,1)`. Fades und kurze Wege; kein Bounce, kein Overshoot, kein Scale über 1.02. Zustandswechsel an Controls in 140ms, Ein-/Ausblenden von Ebenen in 200ms, Reveal-Effekte maximal 520ms.

**Interaktionszustände.** Hover: dunklere Fläche (`--blue-600` beim Primary, `--n-25`/`--n-50` bei Sekundär und Ghost) plus stärkerer Rand — nie Opacity-Änderung. Press: 0,5px nach unten, keine Skalierung. Focus: 3px Blau-Ring (`--focus-ring`) außen, Border bleibt. Disabled: 45 % Deckkraft, `not-allowed`. Destruktiv ist rot als _Text auf Weiß_, niemals als rote Füllfläche.

**Bildsprache.** Keine Fotografie, keine Illustrationen, keine Muster oder Texturen im aktuellen Bestand (es wurden keine Assets geliefert). Gradienten kommen genau einmal vor: als Blau-Verlauf hinter Glas-Demos. Wo Bild stünde, steht große Typografie oder eine ruhige dunkle Fläche. Falls später Fotografie hinzukommt, ist die Vorgabe: kühl-neutral, wenig Sättigung, kein Grain, kein Duotone.

## Iconography

- **System:** [Lucide](https://lucide.dev), 24×24-Grid, 2px Strichstärke, gerundete Enden. Nicht in `assets/` einkopiert, sondern per CDN von `unpkg.com/lucide-static@0.544.0/icons/<slug>.svg` geladen und in der `Icon`-Komponente inline eingesetzt, damit `stroke="currentColor"` greift und Icons in Exporten mitgerastert werden. **Das ist eine Substitution** — es wurde kein Icon-Set geliefert; Lucide passt am besten zur ruhigen, dünn gezeichneten Anmutung.
- **Größen:** 14px (inline, Labels), 16px (Buttons, Navigation), 18px (Standard), 19–24px (Feature-Marken, Empty States).
- **Farbe:** Icons erben immer die Textfarbe des Elternelements. Ein Icon wird nie direkt eingefärbt und nie größer als der Text, den es begleitet.
- **Häufig verwendete Slugs:** `cloud`, `rocket`, `git-branch`, `layout-dashboard`, `scroll-text`, `settings`, `activity`, `search`, `mail`, `arrow-right`, `arrow-up-right`, `chevron-down`, `chevron-right`, `check`, `x`, `trash-2`, `rotate-cw`, `bell`, `book-open`, `external-link`, `more-horizontal`, `chevrons-up-down`, `alert-triangle`, `alert-octagon`, `check-circle`, `info`.
- **Keine Emoji, keine Unicode-Zeichen als Icons.** Ausnahme: `›` und `·` als typografische Trenner in Mono-Zeilen.
- **Kein eigenes Icon-Zeichnen.** Fehlt ein Glyph, wird der nächstliegende Lucide-Slug verwendet.

## Index

**Wurzel**
- `styles.css` — einziger Einstiegspunkt für Konsumenten, nur `@import`-Zeilen.
- `thumbnail.html` — Kachel des Design Systems.
- `readme.md` — dieses Dokument.
- `SKILL.md` — Agent-Skill-Kopf für die Nutzung außerhalb dieses Projekts.

**Tokens** (`tokens/`) — `fonts.css`, `colors.css`, `typography.css`, `spacing.css`, `elevation.css`, `motion.css`, `base.css` (Reset, Body-Defaults, Link-Farben, `.fluer-eyebrow`).

**Komponenten** (`components/`)
- `core/` — **Button**, **IconButton**, **Badge**, **Tag**, **Card**, **Icon**, **Logo**
- `forms/` — **Input** (ein- und mehrzeilig), **Select**, **Checkbox**, **Radio**, **Switch**
- `navigation/` — **Tabs**
- `feedback/` — **Dialog**, **Toast**, **Tooltip**

Jede Komponente: `<Name>.jsx` + `<Name>.d.ts` + `<Name>.prompt.md`, pro Ordner eine `*.card.html`.

*Intentional additions:* `Icon` — Wrapper um das Lucide-Set, damit Glyphen einheitlich über `currentColor` eingefärbt werden und Slugs an einer Stelle dokumentiert sind. `Logo` — das Markenzeichen als Vektor-Komponente, damit es nie als Bilddatei mit eingebrannter Farbe verwendet wird. Alle übrigen Primitives sind der Standardsatz für ein System ohne gelieferte Komponentenquelle.

**Assets** (`assets/`) — `logo.svg`, `logo-wordmark.svg`. Keine Fotografie, keine Illustrationen (nichts geliefert).

**Foundation-Karten** (`guidelines/`) — 19 Karten in den Gruppen Colors, Type, Spacing, Brand.

**UI Kits** (`ui_kits/`)
- `website/` — `SiteChrome.jsx`, `HomePage.jsx`, `index.html`, `README.md`
- `console/` — `AppShell.jsx`, `screens.jsx`, `index.html`, `README.md`

## Offene Punkte

1. **Logo ist ein Entwurf von mir, keine geliefertes Asset.** Auf Wunsch entworfen: eine Wolke (Cloud) mit ausgestanztem Prompt-Zeichen `›_` (Development) — geometrisch aus drei Kreisen und einem Rundrechteck aufgebaut, Aussparung als echte Maske, damit das Zeichen auf jedem Grund funktioniert. Dateien: `assets/logo.svg` (Zeichen), `assets/logo-wordmark.svg` (Zeichen + Wortmarke), Komponente `Logo`. Ich bin Designer, kein Bildgenerator — das ist ein Vektor-Entwurf, der eine Freigabe oder eine Runde Korrekturen braucht (Proportionen der Wolke, Strichstärke des Zeichens, Abstand zur Wortmarke).
2. **Font-Substitution.** Keine Fontdateien geliefert → Geist / Geist Mono über Google Fonts. Bei eigenen Lizenzdateien: `.woff2` nach `assets/fonts/` legen und den `@import` in `tokens/fonts.css` durch lokale `@font-face`-Regeln ersetzen.
3. **Icon-Substitution.** Lucide per CDN, siehe Iconography.
4. **Farbe und Typografie sind ein Vorschlag**, abgeleitet aus der Kurzbeschreibung — kein Bestandsabgleich möglich.
