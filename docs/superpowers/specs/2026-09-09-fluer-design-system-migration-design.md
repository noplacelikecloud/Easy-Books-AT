# Design-Spezifikation: Migration auf das Fluer Design System

- **Datum:** 2026-09-09
- **Status:** Entwurf / Zur Überprüfung
- **Thema:** Umstellung des Easy-Books Frontends auf das Fluer Design System (Deep Blue, warmes Papiergrau, Geist Typografie, Haarlinien, Console AppShell)
- **Referenz:** `docs/Fluer Design System.zip` (entpackt unter `docs/fluer-design-system/`)

---

## 1. Übersicht & Design-Philosophie

Das **Fluer Design System** etabliert ein kompromisslos ruhiges, hochwertiges und präzises Erscheinungsbild für die Easy-Books SaaS-Plattform. Es orientiert sich an modernen B2B-Konsolen (wie Vercel, Linear, Stripe) und ersetzt das bisherige bunte Farb- und Formengemisch durch eine stringente Designsprache:

- **Farbe mit Bedacht:** Ein einziger primärer Akzent: **Deep Blue `#17518C` (`--blue-500`)** für Hauptaktionen, aktive Tabs und Fokusringe. Keine willkürlichen Farbflächen.
- **Natürliche Materialität:** Warme Papiergrau-Töne (`--n-25` `#FBFBF9` für den Seitenhintergrund, `--n-0` `#FFFFFF` für Karten, `--n-100` `#DEDCD7` für Haarlinien).
- **Starke Typografie:** **Geist Sans** mit negativer Laufweite für Headlines und UI-Elemente; **Geist Mono** für Beträge, Währungen, Buchungsnummern und Tabellendaten.
- **Klare Tiefenstaffelung:** Haarlinie (`--border-hairline`) → weicher Schatten (`--shadow-sm`) → Glas-Blur (`--surface-glass`). Nie Schatten ohne Rand.
- **Gezielte Radien:** 3px (Badges, Checkboxen), 6px (IconButtons), 10px (Buttons, Input-Felder), 14px (Karten, Tabellencontainer), 20px (Dialoge). **Keine Pill-Buttons**.
- **Dark Mode:** Ein auf das System abgestimmter Nachtmodus auf Basis von Graphitgrau (`--n-900` `#161614`) und angepassten Kontrasten.

---

## 2. Token-Architektur & Globale Styles

### 2.1 Schriften (`layout.tsx`)
Umstellung von DM Sans auf die Vercel Geist-Schriftfamilie über `next/font/google`:
- `--font-sans`: `Geist({ subsets: ["latin"], variable: "--font-geist-sans" })`
- `--font-mono`: `Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" })`

### 2.2 CSS-Variablen (`globals.css`)

```css
:root {
  /* ── Fluer Neutrals (Warm Paper) ── */
  --n-0:    #ffffff;
  --n-25:   #fbfbf9;
  --n-50:   #f4f3f0;
  --n-75:   #e9e8e4;
  --n-100:  #dedcd7;
  --n-200:  #c7c4bd;
  --n-400:  #8c887f;
  --n-600:  #57544d;
  --n-700:  #3f3d38;
  --n-800:  #282724;
  --n-900:  #161614;

  /* ── Fluer Accent (Deep Blue) ── */
  --blue-50:  #eaf1f7;
  --blue-100: #d0e0ef;
  --blue-200: #a2c2e0;
  --blue-500: #17518c; /* Primär-Akzent */
  --blue-600: #123d6a; /* Hover */
  --blue-700: #0d2c4c;

  /* ── Semantische Zustandsfarben ── */
  --moss-50:  #eef5ed;  --moss-600:  #246e2a; /* Erfolg */
  --amber-50: #fdf6e7;  --amber-600: #8c5d08; /* Warnung */
  --red-50:   #faeceb;  --red-600:   #a33227; /* Gefahr / Storno */
  --petrol-50:#eaf3f5;  --petrol-600:#156170; /* Info */

  /* ── Semantische Mappings für Easy-Books ── */
  --primary:        var(--blue-500);
  --primary-hover:  var(--blue-600);
  --primary-light:  var(--blue-50);
  --bg-page:        var(--n-25);
  --bg-card:        var(--n-0);
  --surface-sunken: var(--n-50);
  --surface-glass:  rgba(255, 255, 255, 0.72);
  --blur-glass:     14px;

  --border-hairline:var(--n-100);
  --border-default: var(--n-200);
  --border-strong:  var(--n-400);

  --text-strong:    var(--n-900);
  --text-body:      var(--n-700);
  --text-muted:     var(--n-600);
  --text-faint:     var(--n-400);

  --focus-ring:     0 0 0 3px var(--blue-100);
  --shadow-xs:      0 1px 2px rgba(22, 22, 20, 0.04);
  --shadow-sm:      0 2px 4px rgba(22, 22, 20, 0.06), 0 1px 2px rgba(22, 22, 20, 0.04);
  --shadow-md:      0 6px 12px -2px rgba(22, 22, 20, 0.08), 0 2px 4px rgba(22, 22, 20, 0.04);
  --shadow-lg:      0 12px 24px -4px rgba(22, 22, 20, 0.12), 0 4px 8px rgba(22, 22, 20, 0.06);

  /* ── Radien ── */
  --radius-xs:   3px;  /* Badges, Checkboxen */
  --radius-sm:   6px;  /* IconButtons, Tags */
  --radius-md:   10px; /* Buttons, Inputs */
  --radius-lg:   14px; /* Cards, Tabellen */
  --radius-xl:   20px; /* Dialoge */
  --radius-pill: 999px;/* Tags, Switches, Avatare */
}

/* ── Fluer Dark Mode (Night Console) ── */
[data-theme="dark"] {
  --bg-page:        var(--n-900);
  --bg-card:        #1e1e1b;
  --surface-sunken: #121210;
  --surface-glass:  rgba(22, 22, 20, 0.75);

  --border-hairline:#2e2e2a;
  --border-default: #3f3d38;
  --border-strong:  #57544d;

  --text-strong:    #f4f3f0;
  --text-body:      #dedcd7;
  --text-muted:     #8c887f;
  --text-faint:     #57544d;

  --primary:        #2373c4;
  --primary-hover:  #2f86de;
  --primary-light:  rgba(23, 81, 140, 0.25);
  --focus-ring:     0 0 0 3px rgba(35, 115, 196, 0.35);
}
```

---

## 3. UI-Komponentenbibliothek (`frontend/src/components/ui/`)

Wir stellen die Fluer-Komponenten als typsichere React/TypeScript (`.tsx`) Komponenten bereit:

### 3.1 Core
1. **`Button` (`ui/core/Button.tsx`)**:
   - Varianten: `primary`, `secondary`, `ghost`, `danger`.
   - Größen: `sm` (30px), `md` (38px), `lg` (46px).
   - Icons: Lucide `icon` (vor Label) oder `iconAfter`.
   - Radius: Feste 10px (`--radius-md`). Keine Pillen!
   - *Danger-Verhalten:* Roter Text auf weißer Karte mit Haarlinie – niemals knallrote Vollfläche.
2. **`IconButton` (`ui/core/IconButton.tsx`)**:
   - Quadratische Aktions-Buttons für Tabellen, Kopfzeilen und Symbolleisten.
3. **`Badge` & `Tag` (`ui/core/Badge.tsx`, `ui/core/Tag.tsx`)**:
   - `Badge`: 3px Radius, dezente Tönung (`neutral`, `brand`, `success`, `warning`, `danger`).
   - `Tag`: 999px Radius, schmale Padding-Werte für Kategorien und Attribute.
4. **`Card` (`ui/core/Card.tsx`)**:
   - 14px Radius, 1px Haarlinie, weicher Schatten (`--shadow-sm`).
   - `interactive`: Hebt bei Hover auf `--shadow-md` und dezent dunkleren Rand.
   - `sunken`: Kein Schatten, eingesenkter Hintergrund (`--surface-sunken`).

### 3.2 Forms
1. **`Input` (`ui/forms/Input.tsx`)**:
   - Ein- und mehrzeilig (Textarea), 10px Radius, Haarlinie, 3px Fokus-Ring.
2. **`Select` (`ui/forms/Select.tsx`)**:
   - Stilistisch auf `Input` abgestimmt, mit standardisiertem `ChevronDown`-Icon.
3. **`Checkbox` & `Radio` (`ui/forms/Checkbox.tsx`, `ui/forms/Radio.tsx`)**:
   - 3px Radius (Checkbox) bzw. rund (Radio), Akzent bei Aktivierung in Deep Blue.
4. **`Switch` (`ui/forms/Switch.tsx`)**:
   - Pill-Form für Einstellungen und Toggles.

### 3.3 Feedback & Navigation
1. **`Dialog` (`ui/feedback/Dialog.tsx`)**:
   - 20px Radius, Scrim mit 3px Blur und 36 % Deckkraft, zentrierte Platzierung.
2. **`Toast` (`ui/feedback/Toast.tsx`)**:
   - Fluer Glas-Fläche mit 14px Blur, weicher Schatten, automatische Ausblendung.
3. **`Tabs` (`ui/navigation/Tabs.tsx`)**:
   - Horizontale Reiter mit Deep Blue Indikator-Linie oder dezenter Kartenhinterlegung.

---

## 4. AppShell & Layout

### 4.1 SideNav (`Sidebar.tsx`)
- **Maße & Fläche:** 264px feste Breite, Hintergrund `--n-25`, rechter Rand `1px solid var(--border-hairline)`.
- **Kopf:** Fluer Wordmark oder Easy-Books Logo mit dezentem `Console`-Badge.
- **Navigationszeilen:**
  - Höhe: 34px, 10px Padding, 16px Lucide-Icons.
  - *Aktiv:* Weißer Kartenhintergrund (`--bg-card`), 1px Haarlinie, feiner Schatten `--shadow-xs`, Schriftgewicht 500.
  - *Inaktiv:* Transparent, Textfarbe `--text-muted`, sanfter Hover auf `--n-50`.
- **Footer:** Mandanten-Monogramm-Pille (`--radius-pill`), Mandantenname, Benutzerrolle und Umschalt-Button (`chevrons-up-down`).

### 4.2 TopBar (`Header.tsx` / `TopNav.tsx`)
- **Höhe:** 60px, sticky fixiert oben.
- **Fläche:** Glas (`--surface-glass`, 72 % Deckkraft + 14px Backdrop-Blur) mit unterer Haarlinie.
- **Links:** Breadcrumb-Pfad (`Bereich › Seite`) mit dezentem Trenner (`chevron-right`).
- **Rechts:** Schnellaktionen (Dokumentation `book-open`, Alerts `bell`, Dark-Mode Toggle `moon`/`sun`) sowie der primäre CTA-Button (`+ Neu`).

### 4.3 Seiten-Layout & Container
- Standardcontainer: max. 1280px mit 32px Gutter.
- Großzügiger Whitespace (32px zwischen logischen Blöcken, 96px zwischen Sektionen).

---

## 5. Arbeitsmasken & Tabellen

### 5.1 Tabellen & Listen (Invoices, Bills, Ledger, Hubs)
- **Container:** Eine zusammenhängende weiße Fläche mit 14px Radius und 1px Haarlinie (`--border-hairline`).
- **Kein Kartenraster:** Datenzeilen werden durch Haarlinien getrennt, nicht durch separate Kacheln.
- **Kopfzeile:** Satzschreibung (kein Title Case), dezente Textfarbe (`--text-muted`).
- **Zahlenformat:** Sämtliche Beträge, Salden, Währungen und Datumsangaben strikt in **Geist Mono**, rechtsbündig ausgerichtet.

### 5.2 Datenerfassungsformulare (Rechnung, Beleg, Stammdaten)
- Überschriften in Semibold mit reduzierter Laufweite.
- Formulargruppen mit 24px Innenabstand in Karten.
- Buttons am Fuß:
  - Primär: `Button variant="primary"` (Deep Blue).
  - Sekundär: `Button variant="secondary"` (Papierweiß).
  - Storno/Löschen: `Button variant="danger"` (Roter Text auf weißer Karte).

---

## 6. Phasenplan zur Umsetzung

1. **Phase 1: Design-Tokens & Typografie**
   - Einbindung der Geist-Fonts in `layout.tsx`.
   - Definition aller Fluer-Tokens und Light/Dark-Variablen in `globals.css`.
   - Sofortige optische Harmonisierung aller bestehenden Seiten.
2. **Phase 2: Komponenten-Bereitstellung**
   - Portierung der Fluer-Komponenten nach `frontend/src/components/ui/` in TypeScript.
3. **Phase 3: AppShell & Navigation**
   - Umbau von `Sidebar.tsx` und `Header.tsx` auf das Fluer Console AppShell Layout.
4. **Phase 4: Schlüssel-Arbeitsmasken**
   - Überarbeitung von Dashboard, Rechnungsmasken (`InvoiceForm.tsx`, `BillForm.tsx`), `LineItemsTable.tsx` und Berichts-Tabellen.
5. **Phase 5: Build- & Docker-Validierung**
   - `npm run build` / TypeScript-Prüfung und Aktualisierung des Docker-Containers.
