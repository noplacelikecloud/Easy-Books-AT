# Design-Spezifikation: Easy-Books MCP Add-on

- **Datum:** 2026-09-09
- **Status:** Entwurf / Zur Überprüfung
- **Thema:** Model Context Protocol (MCP) Server für Buchhaltungs-Abfragen, Belegautomation und Finanz-Workflows

---

## 1. Übersicht & Zielsetzung

Das **Easy-Books MCP Add-on** bindet KI-Modelle (wie Claude Desktop, Cursor, Antigravity oder autonome Agenten) über das standardisierte **Model Context Protocol (MCP)** direkt an das Easy-Books Buchhaltungs-Backend an.

Benutzer können dadurch:
1. **Ihre Buchhaltung im Dialog befragen:** Ad-hoc-Analysen zu GuV, Bilanz, Kontensalden, Cashflow und offenen Posten in natürlicher Sprache stellen.
2. **Geschäftsvorfälle automatisiert erfassen:** Ausgangsrechnungen, Eingangsrechnungen und Journal-Buchungen erstellen und – unter Wahrung aller buchhalterischen Invarianten ($\sum Dr = \sum Cr$) – direkt festschreiben.
3. **Periodische Berichte & Workflows steuern:** Mahnvorschläge für überfällige Forderungen generieren, Kontoauszüge vorkontieren und Liquiditätsprüfungen ausführen.

---

## 2. Architektur & Komponenten

Das System folgt einer hybriden Architektur, die sowohl lokale Ausführung (`stdio`) als auch Cloud-/Docker-Dienste (`sse` über HTTP) unterstützt.

```
+----------------------------------------------------------------------+
|                           KI-Clients                                 |
|   (Claude Desktop, Cursor, Antigravity IDE, autonome Agenten/Skripte) |
+-----------------------------------+----------------------------------+
                                    |
            [stdio (lokal)]         |        [SSE / HTTP (remote)]
                                    v
+----------------------------------------------------------------------+
|                     Easy-Books MCP Server                            |
|             (FastMCP, backend/mcp/, Python 3.11+)                    |
|                                                                      |
|  +---------------------+  +--------------------+  +---------------+  |
|  |     OAuth 2.1       |  |     API Token      |  |  Session &    |  |
|  |   PKCE Client       |  |   (eb_live_...)    |  |  Token Cache  |  |
|  +---------------------+  +--------------------+  +---------------+  |
|                                                                      |
|  Tools:                                                              |
|   - Reports: GuV, Bilanz, SuSa, Kontoblatt, Cash/Bank, Aging        |
|   - Entities: Kontenplan, Kunden, Lieferanten, Belege               |
|   - Transactions: Journal-Buchungen (Dr/Cr), Rechnungen, Zahlungen  |
|   - Workflows: Finanzgesundheit, Mahnwesen, Kontoabstimmung         |
+-----------------------------------+----------------------------------+
                                    |
                    REST API (HTTP / AsyncClient)
                                    v
+----------------------------------------------------------------------+
|                     Easy-Books Backend (FastAPI)                     |
|                                                                      |
|  - Auth & Isolation: routers/common.py:get_current_user              |
|  - OAuth 2.1 Server: routers/oauth_server.py (PKCE S256)             |
|  - Invarianten-Prüfer: services/posting.py (∑Dr = ∑Cr, Periode)      |
|  - Berichte & Ledger: routers/reports.py                             |
+----------------------------------------------------------------------+
```

### Dateistruktur des neuen Moduls:

```
backend/
├── mcp/
│   ├── __init__.py
│   ├── __main__.py          # CLI Einstiegspunkt (python -m backend.mcp)
│   ├── server.py            # FastMCP Server & Tool-Registrierung
│   ├── client.py            # Easy-Books API-Client (HTTPx AsyncClient)
│   ├── config.py            # Konfiguration & Umgebungsvariablen
│   ├── oauth.py             # OAuth 2.1 PKCE Flow Helper (lokaler Callback)
│   └── tools/
│       ├── __init__.py
│       ├── reports.py       # Finanzberichte & Salden
│       ├── entities.py      # Kontenplan & Stammdatensuche
│       ├── transactions.py  # Buchungen, Rechnungen, Zahlungen
│       └── workflows.py     # Mahnwesen, Finanzcheck, Abstimmung
└── routers/
    └── oauth_server.py      # Neuer FastAPI-Router für OAuth 2.1 Endpoints
```

---

## 3. Authentifizierung & Mandantensicherheit

Die Schnittstelle unterstützt zwei redundante, sichere Zugangswege:

### 3.1 OAuth 2.1 (Interaktive Benutzer-Autorisierung)
- **Standard:** OAuth 2.1 mit PKCE (`code_challenge_method=S256`), langlebige Refresh-Tokens, striktes Redirect-URI-Matching.
- **Backend-Erweiterung (`routers/oauth_server.py`):**
  - `GET /api/oauth/authorize`: Prüft Session oder fordert Login; zeigt Bestätigung für Client (`client_id`, z. B. `claude-desktop`) und Mandantenauswahl; generiert ephemeren Authorization Code (Gültigkeit 5 Minuten).
  - `POST /api/oauth/token`: Tauscht Authorization Code + `code_verifier` gegen ein Standard-JWT `access_token` (24h) und ein `refresh_token` (30 Tage).
  - `POST /api/oauth/revoke`: Ermöglicht dem Benutzer das sofortige Entziehen von Tokens.
- **Lokaler Client-Handshake:**
  - Im `stdio`-Modus startet der MCP-Server bei ungesichertem Client einen ephemeren lokalen HTTP-Server (`http://localhost:8089/callback`).
  - Öffnet die Autorisierungsseite im Browser. Nach Abschluss speichert er Tokens verschlüsselt in `~/.easybooks/mcp_tokens.json`.

### 3.2 Service API-Token (`eb_live_...`)
- Headless-Betrieb für Skripte, CI/CD und Docker-Container.
- Nutzt die existierende `ApiKey`-Infrastruktur (`backend/routers/api_keys.py`).
- Übergabe über Umgebungsvariable `EASYBOOKS_API_TOKEN` oder HTTP-Header `Authorization: Bearer eb_live_...`.

### 3.3 Mandanten-Isolation (Tenant Isolation)
- Jeder Aufruf wird im Backend über `get_current_user` aufgelöst.
- Die `tenant_id` wird aus dem JWT oder dem API-Key extrahiert.
- Ein Zugriff auf Daten fremder Mandanten wird auf Datenbankebene mit HTTP 404 (Isolation-Invariant) verhindert.

---

## 4. Werkzeugkatalog (MCP Tools)

### 4.1 Finanzberichte & Abfragen (`tools/reports.py`)

1. **`get_financial_report`**
   - **Parameter:**
     - `report_type`: `"p_and_l"` (GuV) | `"balance_sheet"` (Bilanz) | `"trial_balance"` (Summen- und Saldenliste)
     - `start_date`: `YYYY-MM-DD` (optional für Bilanz)
     - `end_date`: `YYYY-MM-DD`
   - **Rückgabe:** Strukturierte JSON-Hierarchie nach österreichischem UGB (Aktiva/Passiva, Erlöse/Aufwendungen, Salden).

2. **`get_account_ledger`**
   - **Parameter:**
     - `account_code`: z. B. `"2800"` (Bank) oder `"4000"` (Erlöse)
     - `start_date`, `end_date`: Zeitraum
   - **Rückgabe:** Anfangssaldo, chronologische Liste aller Buchungszeilen (Datum, Beleg-Nr., Gegenkonto, Buchungstext, Soll, Haben) und Schlusssaldo.

3. **`get_cash_and_bank_status`**
   - **Parameter:** keine
   - **Rückgabe:** Salden aller Kassa- und Bankkonten, Währungen, Summe der liquiden Mittel.

4. **`get_aging_report`**
   - **Parameter:**
     - `partner_type`: `"customer"` (AR) | `"vendor"` (AP)
   - **Rückgabe:** Summen und Einzellisten aufgeteilt nach Fälligkeitsbändern (*Nicht fällig*, *1–30 Tage*, *31–60 Tage*, *61–90 Tage*, *90+ Tage*).

---

### 4.2 Stammdaten & Suche (`tools/entities.py`)

1. **`search_chart_of_accounts`**
   - **Parameter:** `query` (z. B. `"Reise"`, `"4000"`), `account_type` (optional: `asset`, `liability`, `equity`, `revenue`, `expense`)
   - **Rückgabe:** Passende Konten mit Kontonummer, Bezeichnung und Bildelement.

2. **`search_contacts`**
   - **Parameter:** `type` (`"customer"` | `"vendor"`), `query` (Name, UID, E-Mail)
   - **Rückgabe:** Kontaktdaten, Standard-Zahlungskonditionen, offene Posten.

3. **`search_documents`**
   - **Parameter:** `doc_type` (`"invoice"` | `"bill"` | `"voucher"`), `status` (`"draft"` | `"posted"` | `"overdue"`), `date_from`, `date_to`
   - **Rückgabe:** Liste der passenden Belege mit Metadaten.

---

### 4.3 Buchungen & Belege (`tools/transactions.py`)

1. **`create_journal_entry`**
   - **Parameter:**
     - `date`: `YYYY-MM-DD`
     - `narration`: Buchungstext
     - `lines`: Liste von `{account_code: str, debit: float, credit: float, partner_id?: int}`
     - `voucher_type`: `"JV"` (Standard), `"CP"` / `"CR"`, `"BP"` / `"BR"`
     - `dry_run`: `bool` (Standard `False`)
   - **Validierung:** Erzwingt $\sum Dr = \sum Cr$. Bei `dry_run=True` wird die Buchung nur simuliert und die vorbereitete Buchungsstruktur zurückgegeben.

2. **`create_invoice`**
   - **Parameter:**
     - `customer_id`: int
     - `date`: `YYYY-MM-DD`
     - `due_date`: `YYYY-MM-DD`
     - `items`: Liste von `{product_id?: int, description: str, qty: float, unit_price: float, tax_rate: float}`
     - `post_immediately`: `bool` (Standard `True`, bei `False` Entwurf)
   - **Rückgabe:** Rechnungsnummer, Gesamtbetrag, USt-Aufteilung, Beleg-ID.

3. **`create_bill`**
   - **Parameter:**
     - `vendor_id`: int
     - `bill_number`: Belegnummer des Lieferanten
     - `date`: `YYYY-MM-DD`
     - `due_date`: `YYYY-MM-DD`
     - `items`: Positionen mit Aufwandskonto, Nettobetrag und Vorsteuer
     - `post_immediately`: `bool`
   - **Rückgabe:** Erfasste Verbindlichkeit und Buchungs-ID.

4. **`record_payment`**
   - **Parameter:**
     - `partner_type`: `"customer"` | `"vendor"`
     - `partner_id`: int
     - `bank_account_code`: z. B. `"2800"`
     - `amount`: Zahlungsbetrag
     - `date`: `YYYY-MM-DD`
     - `allocated_invoice_id`: int (optional zum OP-Ausgleich)

---

### 4.4 Automatisierte Workflows (`tools/workflows.py`)

1. **`analyze_financial_health`**
   - **Parameter:** `period` (`"current_month"`, `"last_month"`, `"this_year"`)
   - **Rückgabe:** Kennzahlen wie Liquiditätsgrad, Umsatzrentabilität (%), DSO (Days Sales Outstanding) und Cashflow-Bewertung.

2. **`generate_payment_reminders`**
   - **Parameter:** `min_days_overdue` (Standard `14`), `min_amount` (Standard `50.0`)
   - **Rückgabe:** Liste überfälliger Debitoren inklusive strukturierter Vorlage für Mahnschreiben / E-Mail.

3. **`reconcile_bank_statement`**
   - **Parameter:** `bank_account_code`, `statement_lines: [{date, text, amount, partner_hint}]`
   - **Rückgabe:** Automatische Vorschläge für OP-Zuordnungen und Vorkontierungen zur Bestätigung.

---

## 5. Invarianten & Schutzmechanismen

1. **Kein Direkt-Schreiben ohne Validierung:**
   Alle Buchungen laufen ausnahmslos über `services/posting.py`. Unausgeglichene Buchungen ($\sum Dr \neq \sum Cr$) oder negative Beträge werden strikt mit einer sprechenden Fehlermeldung abgewiesen.
2. **Geschlossene Perioden:**
   Buchungen in abgeschlossene Geschäftsjahre oder gesperrte Perioden werden abgewiesen.
3. **Audit-Trail:**
   Jede durch das MCP Add-on erstellte oder geänderte Entität wird mit `source="mcp"` und der Benutzer-ID im Audit-Protokoll (`AuditLog`) verewigt.
4. **Dry-Run-Unterstützung:**
   Kritische Buchungstools besitzen ein `dry_run`-Flag, das der KI erlaubt, vorab zu prüfen, ob alle Konten existieren und die Buchung formal gültig ist.

---

## 6. Konfiguration & Inbetriebnahme

### 6.1 Claude Desktop Integration (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "easybooks": {
      "command": "python",
      "args": ["-m", "backend.mcp", "--transport", "stdio"],
      "env": {
        "EASYBOOKS_API_URL": "http://localhost:8000",
        "EASYBOOKS_API_TOKEN": "eb_live_xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### 6.2 Docker Integration (`docker-compose.yml`)
```yaml
  mcp-server:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python -m mcp --transport sse --host 0.0.0.0 --port 8001
    environment:
      - EASYBOOKS_API_URL=http://backend:8000
    ports:
      - "8001:8001"
    depends_on:
      - backend
```

---

## 7. Test- & Validierungsstrategie

1. **Unit-Tests (`backend/tests/test_mcp_tools.py`):**
   - Test aller Abfrage-Tools gegen SQLite In-Memory DB mit Mock-Daten.
   - Test der Validierung: Prüfung, dass fehlerhafte Soll/Haben-Summen abgelehnt werden.
2. **OAuth 2.1 PKCE Tests (`backend/tests/test_oauth_server.py`):**
   - Test des Autorisierungscodes, PKCE-Prüfsummen-Validierung und Token-Refresh.
3. **End-to-End Simulation:**
   - Ausführen des MCP-Servers im Stdio-Modus und Absetzen von MCP-Protokoll-JSON-RPC-Requests.
